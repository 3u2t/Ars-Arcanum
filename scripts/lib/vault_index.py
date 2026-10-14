"""Unified VaultIndex and mtime-keyed Data Access Layer for Ars Arcanum (Phase 1 Refactor).

Eliminates duplicated `Path.rglob("*.md")` directory walks across `writing_sprint.py`,
`word_counter.py`, `portfolio.py`, and `omnibus.py` while strictly preserving Ars Arcanum's
invariant engineering contracts (`AGENTS.md`):
- Zero third-party pip runtime dependencies (100% Python >= 3.10 stdlib).
- Strict path traversal defense (`is_safe_subpath`).
- Atomic file writes via staged tempfiles and `os.replace` (`atomic_write`).
- Thread-safe LRU + persistent `.arcanum_cache.json` (`CACHE_VERSION = 3`) memoization.
- Paragraph-aware prose/dialogue/CJK word counting and block-scalar-capable frontmatter parsing.

Repository Target: `scripts/lib/vault_index.py` (or `src/arcanum/core/vault_index.py`)
Reference: https://github.com/aryansinghnagar/Ars-Arcanum
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import sys
import tempfile
import threading
from collections import OrderedDict
from collections.abc import Iterable, Iterator
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# Unify module singleton identity across `scripts.lib.vault_index`, `lib.vault_index`, and `vault_index`
for _alias in ("vault_index", "lib.vault_index", "scripts.lib.vault_index"):
    sys.modules.setdefault(_alias, sys.modules[__name__])

logger = logging.getLogger("arcanum.vault_index")

CACHE_VERSION: int = 3
DEFAULT_EXCLUDED_DIRS: frozenset[str] = frozenset(
    {
        ".arcanum",
        ".git",
        ".obsidian",
        ".trash",
        "__pycache__",
        "Backups",
        "Export",
        "Exports",
        "Scraps",
        "dist",
        "node_modules",
    }
)

# Regex patterns hardened for multi-paragraph dialogue, CriticMarkup, CJK, and thematic breaks
_FRONTMATTER_BOUNDARY_RE = re.compile(r"\A---\s*\r?\n(.*?)\r?\n---\s*(?:\r?\n|\Z)", re.DOTALL)
_CRITIC_DELETE_RE = re.compile(r"\{--.*?--\}", re.DOTALL)
_CRITIC_COMMENT_RE = re.compile(r"\{>>.*?<<\}", re.DOTALL)
_CRITIC_KEEP_RE = re.compile(r"\{\+\+(.*?)\+\+\}|\{==(.*?)==\}|\{~~.*?~>(.*?)~~\}", re.DOTALL)
_NOVELWRITER_DIRECTIVE_RE = re.compile(r"^\s*@[a-zA-Z0-9_]+\s*:\s*(.+?)\s*$", re.MULTILINE)
_THEMATIC_BREAK_RE = re.compile(r"^\s*(?:(?:\*\s*){3,}|(?:-\s*){3,}|(?:_\s*){3,})\s*$", re.MULTILINE)
_CODE_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
_WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#([^\]|]+))?(?:\|([^\]]+))?\]\]")
_CJK_CHAR_RE = re.compile(
    r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff66-\uff9f\uac00-\ud7af]"
)
_WORD_TOKEN_RE = re.compile(r"[A-Za-z0-9]+(?:['’\-][A-Za-z0-9]+)*")
_INLINE_DIALOGUE_SPAN_RE = re.compile(r'(?:“[^”]*”|"[^"\n]*")')


class PathSecurityError(PermissionError):
    """Raised when a path escapes the sovereign vault root."""


def is_safe_subpath(root: Path, candidate: Path) -> bool:
    """Verify that `candidate` resolves strictly inside `root` (path traversal defense)."""
    try:
        resolved_root = root.resolve(strict=False)
        resolved_candidate = candidate.resolve(strict=False)
        return resolved_candidate == resolved_root or resolved_root in resolved_candidate.parents
    except (OSError, RuntimeError, ValueError):
        return False


def atomic_write(target_path: Path, content: str | bytes, encoding: str = "utf-8") -> None:
    """Write `content` atomically to `target_path` via a sibling temporary file and `os.replace`.

    Safely breaks OS hardlinks before replacement so immutable snapshots in `Draft-*` remain intact.
    """
    target_path.parent.mkdir(parents=True, exist_ok=True)
    mode = "wb" if isinstance(content, bytes) else "w"
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{target_path.name}.",
        suffix=".tmp",
        dir=str(target_path.parent),
    )
    tmp_path = Path(tmp_name)
    try:
        if isinstance(content, bytes):
            with os.fdopen(fd, mode) as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
        else:
            with os.fdopen(fd, mode, encoding=encoding, newline="\n") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
        os.replace(str(tmp_path), str(target_path))
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise


def parse_frontmatter(markdown_text: str) -> tuple[dict[str, Any], str]:
    """Zero-dependency YAML frontmatter parser with support for multiline block scalars (`|` and `>`),
    nested dictionaries, inline lists, and typed scalars.
    """
    match = _FRONTMATTER_BOUNDARY_RE.match(markdown_text)
    if not match:
        return {}, markdown_text

    raw_yaml = match.group(1)
    body = markdown_text[match.end() :]
    lines = raw_yaml.splitlines()
    result: dict[str, Any] = {}

    idx = 0
    total = len(lines)

    while idx < total:
        line = lines[idx]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            idx += 1
            continue

        if ":" not in line:
            idx += 1
            continue

        key_part, val_part = line.split(":", 1)
        key = key_part.strip()
        val_str = val_part.strip()

        # Remove trailing comments outside quotes
        if val_str and not val_str.startswith(('"', "'")):
            val_str = re.sub(r"\s+#.*$", "", val_str).strip()

        # Case 1: Multiline block scalar (`|` literal or `>` folded)
        if val_str in ("|", ">", "|-", ">-"):
            fold = val_str.startswith(">")
            strip_trailing = val_str.endswith("-")
            idx += 1
            block_lines: list[str] = []
            base_indent: int | None = None
            while idx < total:
                next_line = lines[idx]
                if not next_line.strip():
                    block_lines.append("")
                    idx += 1
                    continue
                indent = len(next_line) - len(next_line.lstrip(" "))
                if base_indent is None:
                    if indent == 0:
                        break
                    base_indent = indent
                if indent < base_indent:
                    break
                block_lines.append(next_line[base_indent:])
                idx += 1
            joined = " ".join(line.strip() for line in block_lines).strip() if fold else "\n".join(block_lines)
            if strip_trailing:
                joined = joined.rstrip("\n")
            result[key] = joined
            continue

        # Case 2: Indented list or nested mapping on following lines
        if val_str == "":
            idx += 1
            nested_list: list[Any] = []
            nested_dict: dict[str, Any] = {}
            is_list: bool | None = None
            while idx < total:
                next_line = lines[idx]
                next_stripped = next_line.strip()
                if not next_stripped or next_stripped.startswith("#"):
                    idx += 1
                    continue
                indent = len(next_line) - len(next_line.lstrip(" "))
                if indent == 0:
                    break
                if next_stripped.startswith("- "):
                    is_list = True
                    nested_list.append(_coerce_scalar(next_stripped[2:].strip()))
                elif ":" in next_stripped and is_list is not True:
                    is_list = False
                    sub_k, sub_v = next_stripped.split(":", 1)
                    nested_dict[sub_k.strip()] = _coerce_scalar(sub_v.strip())
                idx += 1
            result[key] = nested_list if is_list else nested_dict
            continue

        result[key] = _coerce_scalar(val_str)
        idx += 1

    return result, body


def _coerce_scalar(raw: str) -> Any:
    """Coerce a raw YAML scalar or inline collection into a Python primitive."""
    if not raw:
        return ""
    if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
        return raw[1:-1]
    lower = raw.lower()
    if lower in ("true", "yes"):
        return True
    if lower in ("false", "no"):
        return False
    if lower in ("null", "none", "~"):
        return None
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        return [_coerce_scalar(item.strip()) for item in inner.split(",") if item.strip()]
    if raw.startswith("{") and raw.endswith("}"):
        inner = raw[1:-1].strip()
        if not inner:
            return {}
        out: dict[str, Any] = {}
        for pair in inner.split(","):
            if ":" in pair:
                k, v = pair.split(":", 1)
                out[k.strip()] = _coerce_scalar(v.strip())
        return out
    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        return raw


@dataclass(frozen=True)
class WikilinkRef:
    """Structured representation of an Obsidian wikilink (`[[Target#Heading|Alias]]`)."""

    target: str
    heading: str | None = None
    alias: str | None = None


@dataclass(frozen=True)
class ProseMetrics:
    """Paragraph-aware prose and dialogue telemetry for a single Markdown file."""

    total_words: int
    dialogue_words: int
    narrative_words: int
    cjk_characters: int
    paragraph_count: int
    reading_minutes: float
    audiobook_minutes: float
    paragraph_hashes: tuple[str, ...]

    @property
    def dialogue_ratio(self) -> float:
        if self.total_words == 0:
            return 0.0
        return round(self.dialogue_words / self.total_words, 4)


@dataclass(frozen=True)
class VaultDocumentNode:
    """Cached, immutable snapshot of a parsed Markdown document inside a Sovereign Vault."""

    relative_path: str
    mtime_ns: int
    size_bytes: int
    sha256: str
    frontmatter: dict[str, Any]
    directives: dict[str, str]
    wikilinks: tuple[WikilinkRef, ...]
    metrics: ProseMetrics = field(repr=False)


def compute_prose_metrics(body: str) -> tuple[ProseMetrics, dict[str, str], tuple[WikilinkRef, ...]]:
    """Compute word counts, multi-paragraph-aware dialogue ratios, wikilinks (excluding code blocks),
    and SHA-256 paragraph hashes for fast $O(1)$ hierarchical diffing.
    """
    directives: dict[str, str] = {
        match.group(0).split(":", 1)[0].strip().lstrip("@"): match.group(1).strip()
        for match in _NOVELWRITER_DIRECTIVE_RE.finditer(body)
    }

    body_no_code = _CODE_FENCE_RE.sub("", body)
    wikilinks = tuple(
        WikilinkRef(
            target=m.group(1).strip(),
            heading=m.group(2).strip() if m.group(2) else None,
            alias=m.group(3).strip() if m.group(3) else None,
        )
        for m in _WIKILINK_RE.finditer(body_no_code)
    )

    cleaned = _CRITIC_DELETE_RE.sub("", body_no_code)
    cleaned = _CRITIC_COMMENT_RE.sub("", cleaned)
    cleaned = _CRITIC_KEEP_RE.sub(lambda m: m.group(1) or m.group(2) or m.group(3) or "", cleaned)
    cleaned = _NOVELWRITER_DIRECTIVE_RE.sub("", cleaned)
    cleaned = _THEMATIC_BREAK_RE.sub("", cleaned)

    raw_paragraphs = [p.strip() for p in re.split(r"\r?\n\s*\r?\n", cleaned) if p.strip()]
    paragraph_hashes: list[str] = []
    total_words = 0
    dialogue_words = 0
    cjk_total = 0

    for para in raw_paragraphs:
        if para.startswith("#"):
            continue
        p_hash = hashlib.sha256(para.encode("utf-8")).hexdigest()[:16]
        paragraph_hashes.append(p_hash)

        cjk_count = len(_CJK_CHAR_RE.findall(para))
        latin_words = len(_WORD_TOKEN_RE.findall(para))
        para_words = latin_words + cjk_count
        total_words += para_words
        cjk_total += cjk_count

        stripped_para = para.lstrip()
        if (stripped_para.startswith('"') and stripped_para.count('"') == 1) or (
            stripped_para.startswith("“") and "”" not in stripped_para
        ):
            dialogue_words += para_words
        else:
            for span in _INLINE_DIALOGUE_SPAN_RE.findall(para):
                dialogue_words += len(_WORD_TOKEN_RE.findall(span)) + len(_CJK_CHAR_RE.findall(span))

    dialogue_words = min(dialogue_words, total_words)
    narrative_words = max(0, total_words - dialogue_words)
    metrics = ProseMetrics(
        total_words=total_words,
        dialogue_words=dialogue_words,
        narrative_words=narrative_words,
        cjk_characters=cjk_total,
        paragraph_count=len(paragraph_hashes),
        reading_minutes=round(total_words / 225.0, 2),
        audiobook_minutes=round(total_words / 150.0, 2),
        paragraph_hashes=tuple(paragraph_hashes),
    )
    return metrics, directives, wikilinks


class VaultIndex:
    """Thread-safe, mtime-cached Vault Indexer replacing ad-hoc `rglob('*.md')` walks across Ars Arcanum."""

    def __init__(
        self,
        vault_root: Path,
        cache_file: Path | None = None,
        excluded_dirs: Iterable[str] = DEFAULT_EXCLUDED_DIRS,
        max_memory_entries: int = 2048,
    ) -> None:
        self.vault_root = vault_root.resolve()
        self.cache_file = cache_file or (self.vault_root / ".arcanum_cache.json")
        self.excluded_dirs = frozenset(excluded_dirs)
        self.max_memory_entries = max_memory_entries
        self._lock = threading.RLock()
        self._memory_lru: OrderedDict[str, VaultDocumentNode] = OrderedDict()
        self._load_persistent_cache()

    def iter_markdown_files(self, subpath: Path | None = None) -> Iterator[Path]:
        """Yield all canonical `.md` files inside `vault_root` (or a validated `subpath`)."""
        start = (subpath or self.vault_root).resolve()
        if not is_safe_subpath(self.vault_root, start):
            raise PathSecurityError(f"Refusing to traverse path outside vault root: {start}")

        if start.is_file():
            if start.suffix.lower() == ".md":
                yield start
            return

        for dirpath, dirnames, filenames in os.walk(start):
            dirnames[:] = sorted(d for d in dirnames if d not in self.excluded_dirs and not d.startswith("."))
            for filename in sorted(filenames):
                if filename.endswith(".md") and not filename.startswith("."):
                    candidate = Path(dirpath) / filename
                    if is_safe_subpath(self.vault_root, candidate):
                        yield candidate

    def get_document(self, path: Path) -> VaultDocumentNode:
        """Return a cached or freshly parsed `VaultDocumentNode` in $O(1)$ time when `mtime_ns` is unchanged."""
        resolved = path.resolve()
        if not is_safe_subpath(self.vault_root, resolved):
            raise PathSecurityError(f"Path escapes sovereign vault root: {resolved}")

        stat = resolved.stat()
        rel_key = resolved.relative_to(self.vault_root).as_posix()

        with self._lock:
            cached = self._memory_lru.get(rel_key)
            if cached is not None and cached.mtime_ns == stat.st_mtime_ns and cached.size_bytes == stat.st_size:
                self._memory_lru.move_to_end(rel_key)
                return cached

        raw_bytes = resolved.read_bytes()
        sha256_hex = hashlib.sha256(raw_bytes).hexdigest()
        text = raw_bytes.decode("utf-8", errors="replace")
        frontmatter, body = parse_frontmatter(text)
        metrics, directives, wikilinks = compute_prose_metrics(body)

        node = VaultDocumentNode(
            relative_path=rel_key,
            mtime_ns=stat.st_mtime_ns,
            size_bytes=stat.st_size,
            sha256=sha256_hex,
            frontmatter=frontmatter,
            directives=directives,
            wikilinks=wikilinks,
            metrics=metrics,
        )

        with self._lock:
            self._memory_lru[rel_key] = node
            self._memory_lru.move_to_end(rel_key)
            while len(self._memory_lru) > self.max_memory_entries:
                self._memory_lru.popitem(last=False)

        return node

    def scan_vault(self, subpath: Path | None = None) -> list[VaultDocumentNode]:
        """Index all Markdown files under `subpath` (or the entire vault) and persist the updated cache."""
        nodes = [self.get_document(md_path) for md_path in self.iter_markdown_files(subpath)]
        self.save_persistent_cache()
        return nodes

    def diff_paragraphs_fast(self, old_doc: VaultDocumentNode, new_doc: VaultDocumentNode) -> dict[str, int]:
        """Two-level hierarchical paragraph hash comparison avoiding quadratic `SequenceMatcher` runs."""
        old_set = set(old_doc.metrics.paragraph_hashes)
        new_set = set(new_doc.metrics.paragraph_hashes)
        unchanged = len(old_set & new_set)
        added = len(new_set - old_set)
        removed = len(old_set - new_set)
        return {
            "unchanged_paragraphs": unchanged,
            "added_paragraphs": added,
            "removed_paragraphs": removed,
            "net_word_delta": new_doc.metrics.total_words - old_doc.metrics.total_words,
        }

    def save_persistent_cache(self) -> None:
        """Atomically persist the in-memory index to `.arcanum_cache.json`."""
        if not is_safe_subpath(self.vault_root, self.cache_file):
            raise PathSecurityError(f"Cache file outside vault root: {self.cache_file}")
        with self._lock:
            payload = {
                "cache_version": CACHE_VERSION,
                "vault_root": str(self.vault_root),
                "entries": {
                    key: {
                        "relative_path": node.relative_path,
                        "mtime_ns": node.mtime_ns,
                        "size_bytes": node.size_bytes,
                        "sha256": node.sha256,
                        "frontmatter": node.frontmatter,
                        "directives": node.directives,
                        "wikilinks": [asdict(w) for w in node.wikilinks],
                        "metrics": asdict(node.metrics),
                    }
                    for key, node in self._memory_lru.items()
                },
            }
        atomic_write(self.cache_file, json.dumps(payload, indent=2, sort_keys=True))

    def _load_persistent_cache(self) -> None:
        """Load `.arcanum_cache.json` if present and matching `CACHE_VERSION`."""
        if not self.cache_file.exists():
            return
        try:
            raw = json.loads(self.cache_file.read_text(encoding="utf-8"))
            if raw.get("cache_version") != CACHE_VERSION:
                return
            for key, item in raw.get("entries", {}).items():
                metrics_raw = item["metrics"]
                metrics = ProseMetrics(
                    total_words=int(metrics_raw["total_words"]),
                    dialogue_words=int(metrics_raw["dialogue_words"]),
                    narrative_words=int(metrics_raw["narrative_words"]),
                    cjk_characters=int(metrics_raw["cjk_characters"]),
                    paragraph_count=int(metrics_raw["paragraph_count"]),
                    reading_minutes=float(metrics_raw["reading_minutes"]),
                    audiobook_minutes=float(metrics_raw["audiobook_minutes"]),
                    paragraph_hashes=tuple(metrics_raw["paragraph_hashes"]),
                )
                wikilinks = tuple(WikilinkRef(**w) for w in item.get("wikilinks", []))
                self._memory_lru[key] = VaultDocumentNode(
                    relative_path=item["relative_path"],
                    mtime_ns=int(item["mtime_ns"]),
                    size_bytes=int(item["size_bytes"]),
                    sha256=str(item["sha256"]),
                    frontmatter=dict(item.get("frontmatter", {})),
                    directives=dict(item.get("directives", {})),
                    wikilinks=wikilinks,
                    metrics=metrics,
                )
        except Exception as exc:
            logger.warning("Ignoring corrupt or outdated cache %s: %s", self.cache_file, exc)
