"""Ars Arcanum Manuscript Paragraph-Level Fast Diffing & Draft Lineage Engine.

Module: src/arcanum/manuscript/diff.py
Provides two-level SHA-256 paragraph-hash diffing, scrap extraction,
physical inode separation draft promotion, and draft lineage history.

Engineering Contracts:
- 100% sovereign offline architecture (zero cloud telemetry, zero external pip dependencies).
- Strict path traversal defense with `is_safe_subpath`.
- Atomic writes with Windows backoff retry (`atomic_write`).
- Physical disk inode separation for draft snapshots (`shutil.copy2` with `0o444` parent lock).
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import logging
import os
import re
import shutil
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.arcanum.core.storage import PathSecurityError, atomic_write, is_safe_subpath

logger = logging.getLogger("arcanum.manuscript.diff")

_WORD_RE = re.compile(r"[A-Za-z0-9]+(?:['’\-][A-Za-z0-9]+)*")
_NOVELWRITER_TAG_RE = re.compile(r"^\s*@[a-zA-Z0-9_]+\s*:.*$", re.MULTILINE)
_FRONTMATTER_BOUNDARY_RE = re.compile(r"\A---\s*\r?\n(.*?)\r?\n---\s*(?:\r?\n|\Z)", re.DOTALL)


@dataclass(frozen=True)
class ParagraphDelta:
    """Word-level delta for a single added, deleted, modified, or unchanged paragraph."""

    change_type: str
    old_index: int | None
    new_index: int | None
    old_text: str
    new_text: str
    words_added: int
    words_deleted: int
    similarity_ratio: float


@dataclass(frozen=True)
class ChapterDiffReport:
    """Consolidated diff and churn telemetry between two versions of a chapter."""

    chapter_id: str
    old_word_count: int
    new_word_count: int
    words_added: int
    words_deleted: int
    unchanged_paragraphs: int
    modified_paragraphs: int
    added_paragraphs: int
    deleted_paragraphs: int
    churn_ratio: float
    diagnostics: tuple[str, ...]
    scraps_extracted: tuple[str, ...]
    deltas: tuple[ParagraphDelta, ...]


@dataclass(frozen=True)
class DraftLineageRecord:
    """Historical snapshot lineage metadata for a promoted manuscript draft."""

    draft: str
    parent_draft: str
    milestone: str
    created_at: str
    hardlinked_files: int
    copied_files: int


def parse_frontmatter(markdown_text: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter header and return (frontmatter_dict, markdown_body)."""
    match = _FRONTMATTER_BOUNDARY_RE.match(markdown_text)
    if not match:
        return {}, markdown_text

    raw_yaml = match.group(1)
    body = markdown_text[match.end() :]
    metadata: dict[str, Any] = {}
    for line in raw_yaml.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key_part, val_part = line.split(":", 1)
        key = key_part.strip()
        val_str = val_part.strip()
        if val_str and not val_str.startswith(('"', "'")):
            val_str = re.sub(r"\s+#.*$", "", val_str).strip()
        val_clean = val_str.strip("'\"")
        metadata[key] = val_clean
    return metadata, body


def _split_clean_paragraphs(markdown_text: str) -> list[str]:
    """Strip YAML frontmatter and `@tag:` directives, then split into clean paragraphs."""
    _, body = parse_frontmatter(markdown_text)
    cleaned = _NOVELWRITER_TAG_RE.sub("", body)
    return [p.strip() for p in re.split(r"\r?\n\s*\r?\n", cleaned) if p.strip()]


def _count_words(text: str) -> int:
    return len(_WORD_RE.findall(text))


def _hash_paragraph(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def compare_chapter_hierarchical(
    chapter_id: str,
    old_markdown: str,
    new_markdown: str,
    *,
    scraps_dir: Path | None = None,
    vault_root: Path | None = None,
    min_scrap_words: int = 50,
) -> ChapterDiffReport:
    """Compare two chapter drafts using paragraph hashes first, descending to word-level
    `difflib.SequenceMatcher` only for modified paragraphs.
    """
    old_paras = _split_clean_paragraphs(old_markdown)
    new_paras = _split_clean_paragraphs(new_markdown)

    old_hashes = [_hash_paragraph(p) for p in old_paras]
    new_hashes = [_hash_paragraph(p) for p in new_paras]

    para_matcher = difflib.SequenceMatcher(None, old_hashes, new_hashes, autojunk=False)
    deltas: list[ParagraphDelta] = []
    excised_cuts: list[str] = []

    words_added_total = 0
    words_deleted_total = 0
    unchanged_count = 0
    modified_count = 0
    added_count = 0
    deleted_count = 0

    for tag, i1, i2, j1, j2 in para_matcher.get_opcodes():
        if tag == "equal":
            for offset in range(i2 - i1):
                p_text = old_paras[i1 + offset]
                unchanged_count += 1
                deltas.append(
                    ParagraphDelta(
                        change_type="unchanged",
                        old_index=i1 + offset,
                        new_index=j1 + offset,
                        old_text=p_text,
                        new_text=p_text,
                        words_added=0,
                        words_deleted=0,
                        similarity_ratio=1.0,
                    )
                )
        elif tag == "replace":
            old_span = old_paras[i1:i2]
            new_span = new_paras[j1:j2]
            paired = min(len(old_span), len(new_span))
            for k in range(paired):
                old_p = old_span[k]
                new_p = new_span[k]
                old_tokens = _WORD_RE.findall(old_p)
                new_tokens = _WORD_RE.findall(new_p)
                word_matcher = difflib.SequenceMatcher(None, old_tokens, new_tokens, autojunk=False)
                w_add = 0
                w_del = 0
                for w_tag, wi1, wi2, wj1, wj2 in word_matcher.get_opcodes():
                    if w_tag in ("replace", "delete"):
                        w_del += wi2 - wi1
                    if w_tag in ("replace", "insert"):
                        w_add += wj2 - wj1
                words_added_total += w_add
                words_deleted_total += w_del
                modified_count += 1
                if w_del >= min_scrap_words:
                    excised_cuts.append(old_p)
                deltas.append(
                    ParagraphDelta(
                        change_type="modified",
                        old_index=i1 + k,
                        new_index=j1 + k,
                        old_text=old_p,
                        new_text=new_p,
                        words_added=w_add,
                        words_deleted=w_del,
                        similarity_ratio=round(word_matcher.ratio(), 4),
                    )
                )
            for k in range(paired, len(old_span)):
                old_p = old_span[k]
                w_cnt = _count_words(old_p)
                words_deleted_total += w_cnt
                deleted_count += 1
                if w_cnt >= min_scrap_words:
                    excised_cuts.append(old_p)
                deltas.append(
                    ParagraphDelta(
                        change_type="deleted",
                        old_index=i1 + k,
                        new_index=None,
                        old_text=old_p,
                        new_text="",
                        words_added=0,
                        words_deleted=w_cnt,
                        similarity_ratio=0.0,
                    )
                )
            for k in range(paired, len(new_span)):
                new_p = new_span[k]
                w_cnt = _count_words(new_p)
                words_added_total += w_cnt
                added_count += 1
                deltas.append(
                    ParagraphDelta(
                        change_type="added",
                        old_index=None,
                        new_index=j1 + k,
                        old_text="",
                        new_text=new_p,
                        words_added=w_cnt,
                        words_deleted=0,
                        similarity_ratio=0.0,
                    )
                )
        elif tag == "delete":
            for k in range(i1, i2):
                old_p = old_paras[k]
                w_cnt = _count_words(old_p)
                words_deleted_total += w_cnt
                deleted_count += 1
                if w_cnt >= min_scrap_words:
                    excised_cuts.append(old_p)
                deltas.append(
                    ParagraphDelta(
                        change_type="deleted",
                        old_index=k,
                        new_index=None,
                        old_text=old_p,
                        new_text="",
                        words_added=0,
                        words_deleted=w_cnt,
                        similarity_ratio=0.0,
                    )
                )
        elif tag == "insert":
            for k in range(j1, j2):
                new_p = new_paras[k]
                w_cnt = _count_words(new_p)
                words_added_total += w_cnt
                added_count += 1
                deltas.append(
                    ParagraphDelta(
                        change_type="added",
                        old_index=None,
                        new_index=k,
                        old_text="",
                        new_text=new_p,
                        words_added=w_cnt,
                        words_deleted=0,
                        similarity_ratio=0.0,
                    )
                )

    old_words = sum(_count_words(p) for p in old_paras)
    new_words = sum(_count_words(p) for p in new_paras)
    baseline = max(1, old_words)
    churn_ratio = round((words_added_total + words_deleted_total) / baseline, 4)

    diagnostics: list[str] = []
    if words_added_total == 0 and words_deleted_total == 0:
        diagnostics.append("REV-101: Pristine chapter (zero revision churn detected across drafts).")
    if churn_ratio >= 0.50:
        diagnostics.append(f"REV-102: High structural churn ({churn_ratio * 100:.1f}% word turnover).")
    if words_deleted_total > words_added_total * 1.5 and words_deleted_total >= 100:
        diagnostics.append("REV-103: Heavy compression pass (deletions significantly exceed additions).")
    if words_added_total > old_words * 0.40 and old_words > 0:
        diagnostics.append("REV-104: Major narrative expansion (>40% word growth).")

    saved_scraps: list[str] = []
    if excised_cuts and scraps_dir is not None:
        if vault_root is not None and not is_safe_subpath(vault_root, scraps_dir):
            raise PathSecurityError(f"Scraps directory escapes vault root: {scraps_dir}")
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        safe_stem = re.sub(r"[^A-Za-z0-9_\-]+", "_", chapter_id).strip("_") or "chapter"
        scrap_file = scraps_dir / f"{stamp}_{safe_stem}_scraps.md"
        scrap_body = (
            f"---\nchapter: {chapter_id}\nextracted_at: {stamp}\ncut_blocks: {len(excised_cuts)}\n---\n\n"
            + "\n\n---\n\n".join(excised_cuts)
            + "\n"
        )
        atomic_write(scrap_file, scrap_body)
        saved_scraps.append(str(scrap_file))

    return ChapterDiffReport(
        chapter_id=chapter_id,
        old_word_count=old_words,
        new_word_count=new_words,
        words_added=words_added_total,
        words_deleted=words_deleted_total,
        unchanged_paragraphs=unchanged_count,
        modified_paragraphs=modified_count,
        added_paragraphs=added_count,
        deleted_paragraphs=deleted_count,
        churn_ratio=churn_ratio,
        diagnostics=tuple(diagnostics),
        scraps_extracted=tuple(saved_scraps),
        deltas=tuple(deltas),
    )


def promote_draft_hardlinked(
    manuscript_root: Path,
    parent_draft_name: str,
    new_draft_name: str,
    *,
    milestone_tag: str = "Revision",
    lock_parent: bool = True,
) -> dict[str, Any]:
    """Branch `parent_draft_name` into `new_draft_name` using physical disk copies.

    Adheres strictly to Architectural Contract 2.2: guarantees physical inode separation
    between parent and child drafts. Parent draft files are marked `0o444` read-only.
    """
    root = manuscript_root.resolve()
    parent_dir = root / parent_draft_name
    target_dir = root / new_draft_name

    if not is_safe_subpath(root, parent_dir) or not is_safe_subpath(root, target_dir):
        raise PathSecurityError("Draft directory escapes manuscript root.")
    if not parent_dir.exists():
        raise FileNotFoundError(f"Parent draft does not exist: {parent_dir}")
    if target_dir.exists():
        raise FileExistsError(f"Target draft already exists: {target_dir}")

    linked_files = 0
    for dirpath, dirnames, filenames in os.walk(parent_dir):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        rel_dir = Path(dirpath).relative_to(parent_dir)
        dest_subdir = target_dir / rel_dir
        dest_subdir.mkdir(parents=True, exist_ok=True)

        for fname in filenames:
            if fname == ".locked" or fname.startswith("."):
                continue
            src_file = Path(dirpath) / fname
            dst_file = dest_subdir / fname
            shutil.copy2(src_file, dst_file)
            if lock_parent:
                try:
                    os.chmod(src_file, 0o444)
                except OSError:
                    pass
            linked_files += 1

    stamp = datetime.now(timezone.utc).isoformat()
    lineage_meta = {
        "draft": new_draft_name,
        "parent_draft": parent_draft_name,
        "milestone": milestone_tag,
        "created_at": stamp,
        "hardlinked_files": linked_files,
        "copied_files": linked_files,
    }
    atomic_write(target_dir / ".draft_lineage.json", json.dumps(lineage_meta, indent=2))

    if lock_parent:
        lock_payload = {
            "locked": True,
            "draft": parent_draft_name,
            "promoted_to": new_draft_name,
            "locked_at": stamp,
        }
        atomic_write(parent_dir / ".locked", json.dumps(lock_payload, indent=2))

    return lineage_meta


def get_draft_lineage(manuscript_root: Path, draft_name: str) -> dict[str, Any] | None:
    """Read `.draft_lineage.json` for a specific draft, or None if root draft."""
    root = manuscript_root.resolve()
    draft_dir = root / draft_name
    if not is_safe_subpath(root, draft_dir):
        raise PathSecurityError(f"Draft directory escapes manuscript root: {draft_name}")
    lineage_file = draft_dir / ".draft_lineage.json"
    if not lineage_file.exists():
        return None
    try:
        data = json.loads(lineage_file.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except Exception as exc:
        logger.warning("Failed to parse draft lineage at %s: %s", lineage_file, exc)
    return None


def get_draft_history(manuscript_root: Path, current_draft: str) -> list[dict[str, Any]]:
    """Traverse backward through parent drafts to reconstruct the full draft history chain."""
    history: list[dict[str, Any]] = []
    visited: set[str] = set()
    curr: str | None = current_draft

    while curr and curr not in visited:
        visited.add(curr)
        lineage = get_draft_lineage(manuscript_root, curr)
        if lineage:
            history.append(lineage)
            curr = lineage.get("parent_draft")
        else:
            # Reached root draft without lineage file
            history.append({
                "draft": curr,
                "parent_draft": None,
                "milestone": "Initial Draft",
                "created_at": None,
                "hardlinked_files": 0,
                "copied_files": 0,
            })
            break

    history.reverse()
    return history


def compare_draft_directories(
    parent_draft_dir: Path,
    target_draft_dir: Path,
    *,
    scraps_dir: Path | None = None,
    vault_root: Path | None = None,
    min_scrap_words: int = 50,
) -> list[ChapterDiffReport]:
    """Scan and diff all corresponding Markdown files between two draft directories."""
    reports: list[ChapterDiffReport] = []
    p_dir = parent_draft_dir.resolve()
    t_dir = target_draft_dir.resolve()

    # Discover all Markdown files in parent and target
    p_files = {f.relative_to(p_dir): f for f in p_dir.rglob("*.md") if not f.name.startswith(".")}
    t_files = {f.relative_to(t_dir): f for f in t_dir.rglob("*.md") if not f.name.startswith(".")}

    all_rel_paths = sorted(set(p_files.keys()) | set(t_files.keys()))

    for rel_path in all_rel_paths:
        p_path = p_files.get(rel_path)
        t_path = t_files.get(rel_path)

        old_text = p_path.read_text(encoding="utf-8") if p_path and p_path.exists() else ""
        new_text = t_path.read_text(encoding="utf-8") if t_path and t_path.exists() else ""

        report = compare_chapter_hierarchical(
            chapter_id=str(rel_path),
            old_markdown=old_text,
            new_markdown=new_text,
            scraps_dir=scraps_dir,
            vault_root=vault_root,
            min_scrap_words=min_scrap_words,
        )
        reports.append(report)

    return reports


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for `arcanum diff-fast`."""
    parser = argparse.ArgumentParser(
        prog="arcanum diff-fast",
        description="Run two-level SHA-256 paragraph-hash diffing between two Markdown files.",
    )
    parser.add_argument("old_file", type=Path, help="Baseline Markdown file")
    parser.add_argument("new_file", type=Path, help="Revised Markdown file")
    parser.add_argument("--scraps-dir", type=Path, default=None, help="Optional directory to archive cuts >= 50 words")
    args = parser.parse_args(argv)

    old_md = args.old_file.read_text(encoding="utf-8")
    new_md = args.new_file.read_text(encoding="utf-8")
    report = compare_chapter_hierarchical(
        args.new_file.stem,
        old_md,
        new_md,
        scraps_dir=args.scraps_dir,
    )
    sys.stdout.write(json.dumps(asdict(report), indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
