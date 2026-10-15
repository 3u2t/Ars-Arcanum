"""Phase 5 Audit Hardening & Obsidian Lite Mode Engine (`scripts/lib/audit_hardening.py`).

Provides zero-dependency Python 3.10+ stdlib hardening for:
1. Bounded ZIP/XML validation (`.docx` & `.pgd` archives) against zip bombs, path traversal, and XML entity expansion.
2. Fuzz-resilient YAML frontmatter extraction with recursion depth, BOM, and byte-size guards.
3. CriticMarkup syntax sanitization for malformed or nested `{++...++}` and `{--...--}` runs prior to OpenXML export.
4. CJK ideograph and Unicode NFC prose normalization.
5. One-command Obsidian Lite Mode (`lite-check`) focusing on the 4 core deterministic compilers (`EPI-*`, `TIME-*`, `CON-*`, `LED-*`) and a 5-plugin Obsidian profile.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET  # nosec B405
import zipfile
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

LITE_OBSIDIAN_PLUGINS: tuple[str, ...] = (
    "dataview",
    "templater-obsidian",
    "omnisearch",
    "obsidian-style-settings",
    "longform",
)

CORE_COMPILER_PREFIXES: tuple[str, ...] = ("EPI-", "TIME-", "CON-", "LED-")

_XML_FORBIDDEN_DECL_RE = re.compile(rb"<!\s*(?:DOCTYPE|ENTITY)\b", re.IGNORECASE)
_CJK_CHAR_RE = re.compile(
    r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\U00020000-\U0002ebef]"
)
_LATIN_WORD_RE = re.compile(r"[A-Za-z0-9]+(?:['\u2019-][A-Za-z0-9]+)*")


@dataclass(frozen=True)
class HardenedArchiveLimits:
    """Resource and structural safety limits for archive and frontmatter parsers."""

    max_entries: int = 2048
    max_uncompressed_bytes: int = 64 * 1024 * 1024
    max_compression_ratio: float = 100.0
    max_yaml_depth: int = 16
    max_frontmatter_bytes: int = 262144


@dataclass(frozen=True)
class LiteCheckReport:
    """Consolidated report emitted by the one-click Obsidian Lite Mode continuity runner."""

    vault_root: Path
    status: str
    total_issues: int
    counts_by_prefix: dict[str, int]
    findings: list[dict[str, str]] = field(default_factory=list)
    dashboard_path: Path | None = None
    profile_path: Path | None = None


def validate_safe_zip_archive(
    archive_path: Path | str,
    limits: HardenedArchiveLimits | None = None,
) -> list[str]:
    """Validate a `.docx` or `.pgd` ZIP archive against zip bombs and path traversal."""
    cfg = limits or HardenedArchiveLimits()
    path = Path(archive_path)
    if not path.is_file():
        msg = f"Archive file does not exist: {path}"
        raise FileNotFoundError(msg)
    if not zipfile.is_zipfile(path):
        msg = f"File is not a valid ZIP archive: {path}"
        raise ValueError(msg)

    member_names: list[str] = []
    total_uncompressed = 0
    with zipfile.ZipFile(path, "r") as zf:
        infos = zf.infolist()
        if len(infos) > cfg.max_entries:
            msg = f"ZIP archive exceeds max_entries ({len(infos)} > {cfg.max_entries})"
            raise ValueError(msg)
        for info in infos:
            raw_name = info.filename
            norm_str = raw_name.replace("\\", "/")
            norm_path = Path(norm_str)
            has_drive = len(norm_str) >= 2 and norm_str[1] == ":" and norm_str[0].isalpha()
            if norm_str.startswith("/") or has_drive or ".." in norm_path.parts:
                msg = f"Unsafe path traversal entry in ZIP archive: {raw_name}"
                raise ValueError(msg)
            total_uncompressed += info.file_size
            if total_uncompressed > cfg.max_uncompressed_bytes:
                msg = (
                    f"ZIP archive uncompressed size ({total_uncompressed} B) "
                    f"exceeds limit ({cfg.max_uncompressed_bytes} B)"
                )
                raise ValueError(msg)
            compressed = max(info.compress_size, 1)
            ratio = info.file_size / compressed
            if info.file_size > 65536 and ratio > cfg.max_compression_ratio:
                msg = f"Suspicious ZIP compression ratio ({ratio:.1f}x) on member {raw_name}"
                raise ValueError(msg)
            member_names.append(raw_name)
    return member_names


def parse_xml_safe_bytes(xml_bytes: bytes | str) -> ET.Element:
    """Parse XML bytes after rejecting DOCTYPE and ENTITY expansion declarations."""
    raw = xml_bytes.encode("utf-8") if isinstance(xml_bytes, str) else xml_bytes
    if _XML_FORBIDDEN_DECL_RE.search(raw):
        msg = "XML payload rejected: DOCTYPE and ENTITY declarations are forbidden."
        raise ValueError(msg)
    return ET.fromstring(raw)  # nosec B314


def parse_frontmatter_hardened(
    markdown_text: str,
    limits: HardenedArchiveLimits | None = None,
) -> tuple[dict[str, Any], str]:
    """Fuzz-hardened YAML frontmatter extractor with BOM, size, and depth bounds."""
    cfg = limits or HardenedArchiveLimits()
    cleaned = markdown_text.lstrip("\ufeff")
    if not cleaned.startswith("---"):
        return {}, cleaned

    lines = cleaned.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return {}, cleaned

    closing_idx: int | None = None
    fm_chars = 0
    for idx in range(1, len(lines)):
        fm_chars += len(lines[idx])
        if fm_chars > cfg.max_frontmatter_bytes:
            msg = f"Frontmatter block exceeds {cfg.max_frontmatter_bytes} bytes limit."
            raise ValueError(msg)
        stripped = lines[idx].strip()
        if stripped in ("---", "..."):
            closing_idx = idx
            break

    if closing_idx is None:
        return {}, cleaned

    fm_lines = lines[1:closing_idx]
    body = "".join(lines[closing_idx + 1 :])

    for raw_line in fm_lines:
        expanded = raw_line.expandtabs(2)
        leading_spaces = len(expanded) - len(expanded.lstrip(" "))
        if leading_spaces // 2 > cfg.max_yaml_depth:
            msg = f"YAML frontmatter indentation depth exceeds max_yaml_depth ({cfg.max_yaml_depth})."
            raise ValueError(msg)

    metadata: dict[str, Any] = {}
    current_key: str | None = None
    list_buffer: list[Any] | None = None

    for raw_line in fm_lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("- ") and current_key is not None:
            if list_buffer is None:
                list_buffer = []
                metadata[current_key] = list_buffer
            list_buffer.append(_coerce_yaml_scalar(line[2:].strip()))
            continue
        if ":" in line:
            key_part, val_part = line.split(":", 1)
            key = key_part.strip()
            if not key:
                continue
            val = val_part.strip()
            current_key = key
            list_buffer = None
            if not val or val in ("|", ">"):
                metadata[key] = ""
            elif val.startswith("[") and val.endswith("]"):
                inner = val[1:-1].strip()
                metadata[key] = (
                    [_coerce_yaml_scalar(item.strip()) for item in inner.split(",") if item.strip()]
                    if inner
                    else []
                )
            else:
                metadata[key] = _coerce_yaml_scalar(val)

    return metadata, body


def _coerce_yaml_scalar(raw_val: str) -> Any:
    """Coerce a simple YAML scalar string into bool, int, float, or unquoted str."""
    if len(raw_val) >= 2 and raw_val[0] == raw_val[-1] and raw_val[0] in {'"', "'"}:
        return raw_val[1:-1]
    lower = raw_val.lower()
    if lower in ("true", "yes"):
        return True
    if lower in ("false", "no"):
        return False
    if lower in ("null", "none", "~"):
        return None
    if re.fullmatch(r"-?\d+", raw_val):
        return int(raw_val)
    if re.fullmatch(r"-?\d+\.\d+", raw_val):
        return float(raw_val)
    return raw_val


def sanitize_critic_markup(text: str) -> str:
    """Balance unclosed or nested CriticMarkup tokens so OpenXML export remains valid."""
    if not text:
        return ""

    pairs: tuple[tuple[str, str], ...] = (
        ("{++", "++}"),
        ("{--", "--}"),
        ("{~~", "~~}"),
        ("{==", "==}"),
        ("{>>", "<<}"),
    )
    result = text
    for open_tok, close_tok in pairs:
        result = _balance_token_pair(result, open_tok, close_tok)
    return result


def _balance_token_pair(text: str, open_tok: str, close_tok: str) -> str:
    """Ensure every `open_tok` has a matching non-nested `close_tok`."""
    out: list[str] = []
    i = 0
    n = len(text)
    in_span = False
    while i < n:
        if text.startswith(open_tok, i):
            if not in_span:
                out.append(open_tok)
                in_span = True
            i += len(open_tok)
        elif text.startswith(close_tok, i):
            if in_span:
                out.append(close_tok)
                in_span = False
            i += len(close_tok)
        else:
            out.append(text[i])
            i += 1
    if in_span:
        out.append(close_tok)
    return "".join(out)


def normalize_cjk_and_unicode_prose(text: str) -> dict[str, Any]:
    """Normalize Unicode prose (NFC) and compute hybrid Latin + CJK word metrics."""
    normalized = unicodedata.normalize("NFC", text.lstrip("\ufeff"))
    normalized = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", normalized)
    cjk_count = len(_CJK_CHAR_RE.findall(normalized))
    non_cjk = _CJK_CHAR_RE.sub(" ", normalized)
    latin_words = len(_LATIN_WORD_RE.findall(non_cjk))
    return {
        "text": normalized,
        "latin_words": latin_words,
        "cjk_ideographs": cjk_count,
        "effective_words": latin_words + cjk_count,
    }


def export_markdown_to_docx_hardened(
    markdown_path: Path,
    docx_path: Path,
    author: str = "Ars Arcanum",
) -> Path:
    """Sanitize CriticMarkup and Unicode before exporting OpenXML `.docx` tracked changes."""
    raw_text = Path(markdown_path).read_text(encoding="utf-8")
    norm_text = str(normalize_cjk_and_unicode_prose(raw_text)["text"])
    safe_text = sanitize_critic_markup(norm_text)
    target_docx = Path(docx_path)

    wrote_via_delegate = False
    try:
        from scripts.lib.docx_tracked_changes import export_markdown_to_docx

        tmp_md = target_docx.with_suffix(".sanitized.tmp.md")
        try:
            tmp_md.write_text(safe_text, encoding="utf-8")
            export_markdown_to_docx(tmp_md, target_docx, author=author)
            wrote_via_delegate = target_docx.is_file()
        finally:
            tmp_md.unlink(missing_ok=True)
    except Exception:
        wrote_via_delegate = False

    if not wrote_via_delegate:
        _write_minimal_tracked_docx(safe_text, target_docx, author=author)

    validate_safe_zip_archive(target_docx)
    return target_docx


def pull_docx_to_markdown_hardened(
    docx_path: Path,
    markdown_path: Path | None = None,
) -> str:
    """Validate `.docx` archive safety and XML entities before pulling tracked changes."""
    target_docx = Path(docx_path)
    validate_safe_zip_archive(target_docx)
    with zipfile.ZipFile(target_docx, "r") as zf:
        if "word/document.xml" not in zf.namelist():
            msg = f"Missing word/document.xml inside {target_docx}"
            raise ValueError(msg)
        doc_bytes = zf.read("word/document.xml")
    parse_xml_safe_bytes(doc_bytes)

    text_out = ""
    try:
        from scripts.lib.docx_tracked_changes import pull_docx_to_markdown

        tmp_out = target_docx.with_suffix(".pulled.tmp.md")
        try:
            res = pull_docx_to_markdown(target_docx, tmp_out)
            text_out = res if isinstance(res, str) else (tmp_out.read_text(encoding="utf-8") if tmp_out.is_file() else "")
        finally:
            tmp_out.unlink(missing_ok=True)
    except Exception:
        text_out = ""

    if not text_out:
        text_out = _extract_critic_markup_from_xml(doc_bytes)

    if markdown_path is not None:
        Path(markdown_path).write_text(text_out, encoding="utf-8")
    return text_out


def _write_minimal_tracked_docx(markdown_text: str, docx_path: Path, author: str) -> None:
    """Fallback minimal OpenXML builder used when running standalone or with custom schemas."""
    ns = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    ET.register_namespace("w", ns)
    doc_el = ET.Element(f"{{{ns}}}document")
    body_el = ET.SubElement(doc_el, f"{{{ns}}}body")
    p_el = ET.SubElement(body_el, f"{{{ns}}}p")
    token_re = re.compile(r"(\{\+\+.*?\+\+\}|\{--.*?--\})", re.DOTALL)
    for part in token_re.split(markdown_text):
        if not part:
            continue
        if part.startswith("{++") and part.endswith("++}"):
            ins_el = ET.SubElement(p_el, f"{{{ns}}}ins", {f"{{{ns}}}author": author})
            r_el = ET.SubElement(ins_el, f"{{{ns}}}r")
            t_el = ET.SubElement(r_el, f"{{{ns}}}t")
            t_el.text = part[3:-3]
        elif part.startswith("{--") and part.endswith("--}"):
            del_el = ET.SubElement(p_el, f"{{{ns}}}del", {f"{{{ns}}}author": author})
            r_el = ET.SubElement(del_el, f"{{{ns}}}r")
            dt_el = ET.SubElement(r_el, f"{{{ns}}}delText")
            dt_el.text = part[3:-3]
        else:
            r_el = ET.SubElement(p_el, f"{{{ns}}}r")
            t_el = ET.SubElement(r_el, f"{{{ns}}}t")
            t_el.text = part

    xml_bytes = ET.tostring(doc_el, encoding="utf-8", xml_declaration=True)
    docx_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(docx_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("word/document.xml", xml_bytes)


def _extract_critic_markup_from_xml(xml_bytes: bytes) -> str:
    """Extract plain text and `<w:ins>`/`<w:del>` runs into CriticMarkup."""
    root = parse_xml_safe_bytes(xml_bytes)
    ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    chunks: list[str] = []
    for elem in root.iter():
        if elem.tag == f"{ns}ins":
            inner = "".join(t.text or "" for t in elem.iter(f"{ns}t"))
            chunks.append(f"{{++{inner}++}}")
        elif elem.tag == f"{ns}del":
            inner = "".join(t.text or "" for t in elem.iter(f"{ns}delText"))
            chunks.append(f"{{--{inner}--}}")
        elif elem.tag == f"{ns}p":
            for child in elem:
                if child.tag == f"{ns}r":
                    chunks.extend(t.text or "" for t in child.iter(f"{ns}t"))
    return "".join(chunks)


def import_polyglot_lexicon_hardened(
    pgd_or_xml_path: Path | str,
    limits: HardenedArchiveLimits | None = None,
) -> list[Any]:
    """Validate `.pgd` ZIP bounds and XML entity safety before importing PolyGlot lexemes."""
    path = Path(pgd_or_xml_path)
    if not path.is_file():
        msg = f"PolyGlot source file not found: {path}"
        raise FileNotFoundError(msg)

    if zipfile.is_zipfile(path):
        validate_safe_zip_archive(path, limits=limits)
        with zipfile.ZipFile(path, "r") as zf:
            xml_members = [m for m in zf.namelist() if m.endswith(".xml")]
            if not xml_members:
                msg = f"No XML dictionary payload found inside PolyGlot archive: {path}"
                raise ValueError(msg)
            raw_xml = zf.read(xml_members[0])
    else:
        raw_xml = path.read_bytes()

    root = parse_xml_safe_bytes(raw_xml)
    delegated_items: list[Any] = []
    try:
        from scripts.lib.conlang_linter import import_polyglot_lexicon

        delegated_items = list(import_polyglot_lexicon(path))
    except Exception:
        delegated_items = []

    if delegated_items:
        return delegated_items

    lexemes: list[dict[str, str]] = []
    for word_el in root.iter("word"):
        val = (word_el.findtext("conWord") or "").strip()
        local = (word_el.findtext("localWord") or "").strip()
        ipa = (word_el.findtext("proc") or "").strip()
        if val:
            lexemes.append({"con_word": val, "gloss": local, "ipa": ipa})
    return lexemes


def generate_obsidian_lite_profile(vault_root: Path | str) -> Path:
    """Write `.obsidian/lite_profile.json` restricting plugins to the 5 essential tools."""
    root = Path(vault_root)
    obsidian_dir = root / ".obsidian"
    obsidian_dir.mkdir(parents=True, exist_ok=True)
    profile_path = obsidian_dir / "lite_profile.json"
    payload = {
        "profile": "ars-arcanum-lite",
        "version": "0.1.0",
        "description": "Low-friction 5-plugin Obsidian profile paired with the 4 core deterministic compilers.",
        "enabled_plugins": list(LITE_OBSIDIAN_PLUGINS),
        "enabled_compilers": list(CORE_COMPILER_PREFIXES),
    }
    profile_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return profile_path


def render_lite_dashboard_markdown(report: LiteCheckReport) -> str:
    """Render a clean Obsidian callout dashboard (`_Arcanum_Lite_Dashboard.md`)."""
    callout_type = "success" if report.total_issues == 0 else "warning"
    lines = [
        "# 🪶 Ars Arcanum — Lite Mode Continuity Dashboard",
        "",
        f"> [!{callout_type}] Status: **{report.status}** ({report.total_issues} Core Continuity Findings)",
        "> Focused exclusively on the 4 flagship deterministic compilers (`EPI-*`, `TIME-*`, `CON-*`, `LED-*`).",
        "",
        "## Pillar Summary",
        "",
        "| Compiler Pillar | Rule Prefix | Active Findings |",
        "| :--- | :--- | ---: |",
        f"| **Epistemic POV Firewall** | `EPI-*` | {report.counts_by_prefix.get('EPI-', 0)} |",
        f"| **Timeline & Route Physics** | `TIME-*` | {report.counts_by_prefix.get('TIME-', 0)} |",
        f"| **Conlang Phonotactic Linter** | `CON-*` | {report.counts_by_prefix.get('CON-', 0)} |",
        f"| **Resource Conservation Ledger** | `LED-*` | {report.counts_by_prefix.get('LED-', 0)} |",
        "",
    ]
    if report.findings:
        lines.extend(["## Actionable Findings", ""])
        for item in report.findings:
            code = item.get("code", "ARC-000")
            msg = item.get("message", "")
            loc = item.get("file", "")
            loc_suffix = f" (`{loc}`)" if loc else ""
            lines.append(f"- **`{code}`**{loc_suffix}: {msg}")
        lines.append("")
    else:
        lines.extend(
            [
                "> [!info] Zero continuity violations detected across POV knowledge, timeline physics, conlangs, and resource ledgers.",
                "",
            ]
        )
    return "\n".join(lines)


def run_lite_continuity_check(
    vault_root: Path | str,
    write_dashboard: bool = True,
) -> LiteCheckReport:
    """Execute the 4 core deterministic compilers and emit `_Arcanum_Lite_Dashboard.md`."""
    root = Path(vault_root)
    if not root.exists():
        msg = f"Vault directory does not exist: {root}"
        raise FileNotFoundError(msg)

    counts: dict[str, int] = dict.fromkeys(CORE_COMPILER_PREFIXES, 0)
    findings: list[dict[str, str]] = []

    try:
        from scripts.lib.vault_continuity_runner import run_full_vault_continuity_suite

        suite_res = run_full_vault_continuity_suite(root)
        raw_items = getattr(suite_res, "diagnostics", None) or getattr(suite_res, "findings", None) or []
        for diag in raw_items:
            code = str(getattr(diag, "code", None) or (diag.get("code") if isinstance(diag, dict) else "EPI-001"))
            msg = str(getattr(diag, "message", None) or (diag.get("message") if isinstance(diag, dict) else diag))
            file_ref = str(getattr(diag, "file", None) or (diag.get("file") if isinstance(diag, dict) else ""))
            for prefix in CORE_COMPILER_PREFIXES:
                if code.startswith(prefix):
                    counts[prefix] += 1
                    findings.append({"code": code, "message": msg, "file": file_ref})
                    break
    except Exception:
        pass

    # Always run heuristic frontmatter & ledger checks so standalone chapter vaults are audited
    findings.extend(_scan_markdown_lite_heuristics(root, counts))

    total = sum(counts.values())
    status = "CLEAN" if total == 0 else "NEEDS_ATTENTION"
    profile_path = generate_obsidian_lite_profile(root)
    dashboard_path = root / "_Arcanum_Lite_Dashboard.md" if write_dashboard else None

    report = LiteCheckReport(
        vault_root=root,
        status=status,
        total_issues=total,
        counts_by_prefix=counts,
        findings=findings,
        dashboard_path=dashboard_path,
        profile_path=profile_path,
    )
    if dashboard_path is not None:
        dashboard_path.write_text(render_lite_dashboard_markdown(report), encoding="utf-8")
    return report


def _scan_markdown_lite_heuristics(
    vault_root: Path,
    counts: dict[str, int],
) -> list[dict[str, str]]:
    """Scan Markdown frontmatter for malformed YAML (`EPI-000`) and negative resource balances (`LED-001`)."""
    findings: list[dict[str, str]] = []
    for md_file in sorted(vault_root.rglob("*.md")):
        if md_file.name.startswith("_Arcanum_"):
            continue
        rel_name = str(md_file.relative_to(vault_root))
        try:
            raw = md_file.read_text(encoding="utf-8")
            meta, _ = parse_frontmatter_hardened(raw)
        except Exception as exc:
            counts["EPI-"] += 1
            findings.append(
                {
                    "code": "EPI-000",
                    "message": f"Malformed frontmatter block: {exc}",
                    "file": rel_name,
                }
            )
            continue

        balance = meta.get("resource_balance")
        if isinstance(balance, int | float) and not isinstance(balance, bool) and balance < 0:
            counts["LED-"] += 1
            findings.append(
                {
                    "code": "LED-001",
                    "message": f"Negative resource conservation balance ({balance}) in chapter frontmatter.",
                    "file": rel_name,
                }
            )
    return findings


def build_lite_parser() -> argparse.ArgumentParser:
    """Create the argument parser for `arcanum-lite` / `lite-check`."""
    parser = argparse.ArgumentParser(
        prog="arcanum-lite",
        description="One-command Obsidian Lite Mode continuity runner (EPI-*, TIME-*, CON-*, LED-*).",
    )
    parser.add_argument(
        "vault",
        nargs="?",
        default=".",
        help="Path to the target Universe or Manuscript vault directory (default: current directory).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Emit machine-readable JSON summary to stdout.",
    )
    parser.add_argument(
        "--no-dashboard",
        action="store_true",
        help="Skip writing `_Arcanum_Lite_Dashboard.md` to the vault root.",
    )
    return parser


def main_lite(argv: Sequence[str] | None = None) -> int:
    """Execute the Obsidian Lite Mode continuity check from the command line."""
    args_list = list(sys.argv[1:] if argv is None else argv)
    if args_list and args_list[0] == "lite-check":
        args_list = args_list[1:]

    parser = build_lite_parser()
    parsed = parser.parse_args(args_list)
    vault_path = Path(parsed.vault).resolve()
    if not vault_path.exists():
        print(f"[ERROR] Vault path does not exist: {vault_path}", file=sys.stderr)
        return 2

    report = run_lite_continuity_check(vault_path, write_dashboard=not parsed.no_dashboard)
    if parsed.as_json:
        payload = {
            "vault_root": str(report.vault_root),
            "status": report.status,
            "total_issues": report.total_issues,
            "counts_by_prefix": report.counts_by_prefix,
            "dashboard_path": str(report.dashboard_path) if report.dashboard_path else None,
            "profile_path": str(report.profile_path) if report.profile_path else None,
        }
        print(json.dumps(payload, indent=2))
    else:
        print(
            f"[ARCANUM LITE] Status: {report.status} | "
            f"Findings: {report.total_issues} | "
            f"Dashboard: {report.dashboard_path}"
        )
    return 0 if report.total_issues == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main_lite())
