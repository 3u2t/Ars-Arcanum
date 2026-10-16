#!/usr/bin/env python3
"""
Ars Arcanum High-Performance Cache & Data Access Layer (src/arcanum/core/cache.py)
==================================================================================
Thread-safe, mtime-keyed in-memory & on-disk cache layer and centralized Data Access
Layer (DAL) for World Bibles and Manuscripts.

Key Features:
1. Memoized and bounded Markdown parsing with tag extraction, wikilink resolution,
   and frontmatter caching.
2. Thread-safe LRU bounds with auto-invalidation on file mutation.
3. Fast project scanning and aggregated wordcount telemetry.
4. Centralized DataAccessLayer singleton (`get_data_access()`).

100% Sovereign Offline Architecture — Zero Pip Dependencies.
"""

from __future__ import annotations

import argparse
from collections import OrderedDict
from dataclasses import dataclass
import json
import logging
import os
from pathlib import Path
import re
import sys
import threading
from typing import Any

from src.arcanum.core.frontmatter import (
    extract_frontmatter_and_body,
    parse_yaml_document,
    parse_yaml_frontmatter,
)
from src.arcanum.core.storage import atomic_write

logger = logging.getLogger("arcanum.core.cache")

CACHE_VERSION: int = 2
CACHE_FILENAME: str = ".arcanum_cache.json"
MAX_BYTES: int = 4 * 1024 * 1024

EXCLUDE_DIR_NAMES: frozenset[str] = frozenset({
    ".obsidian", ".git",
    "Exports", "04-Publishing", "04_Publishing",
    "Backups", "05-Backups", "05_Backups",
    "04_Back_Matter", "04-Back-Matter",
})

TAG_REGEXES: dict[str, re.Pattern[str]] = {
    "pov": re.compile(r"^@pov:\s*(.+)$", re.IGNORECASE | re.MULTILINE),
    "characters": re.compile(r"^@(?:chars?|characters?):\s*(.+)$", re.IGNORECASE | re.MULTILINE),
    "location": re.compile(r"^@(?:location|loc|setting):\s*(.+)$", re.IGNORECASE | re.MULTILINE),
    "thread": re.compile(r"^@(?:thread|subplot|plot):\s*(.+)$", re.IGNORECASE | re.MULTILINE),
    "status": re.compile(r"^@(?:status|state):\s*(.+)$", re.IGNORECASE | re.MULTILINE),
    "time": re.compile(r"^@(?:time|date|era):\s*(.+)$", re.IGNORECASE | re.MULTILINE),
}

TAG_KEY_MAP: dict[str, str] = {
    "pov": "pov",
    "char": "characters",
    "chars": "characters",
    "character": "characters",
    "characters": "characters",
    "location": "location",
    "loc": "location",
    "setting": "location",
    "thread": "thread",
    "subplot": "thread",
    "plot": "thread",
    "status": "status",
    "state": "status",
    "time": "time",
    "date": "time",
    "era": "time",
}

TAG_LINE_REGEX: re.Pattern[str] = re.compile(r"^@([A-Za-z0-9_-]+):\s*(.+)$", re.MULTILINE)
WIKILINK_REGEX: re.Pattern[str] = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\\?\|[^\]]+)?\]\]")
FRONTMATTER_REGEX: re.Pattern[str] = re.compile(r"^---\s*\r?\n(.*?)\r?\n---\s*(?:\r?\n|$)", re.DOTALL)
FENCED_CODE_REGEX: re.Pattern[str] = re.compile(r"```.*?```", re.DOTALL)
WORD_REGEX: re.Pattern[str] = re.compile(r"\b\w+\b", re.UNICODE)
NW_TAG_LINE_REGEX: re.Pattern[str] = re.compile(r"^@[A-Za-z0-9_-]+:")


def count_prose_words(text: str) -> int:
    """Canonical Unicode-aware prose word counter across all Ars Arcanum engines."""
    if not text:
        return 0
    clean = FRONTMATTER_REGEX.sub("", text)
    clean = FENCED_CODE_REGEX.sub("", clean)
    clean = re.sub(r"<!--[\s\S]*?-->", "", clean)
    lines: list[str] = []
    for ln in clean.splitlines():
        s = ln.strip()
        if not s:
            continue
        if s.startswith("@") and NW_TAG_LINE_REGEX.match(s):
            continue
        if s.startswith("%"):
            continue
        lines.append(s)
    clean_text = "\n".join(lines)
    return len(WORD_REGEX.findall(clean_text))


def count_words(text: str) -> int:
    """Canonical word count alias."""
    return count_prose_words(text)


def extract_tags(content: str) -> dict[str, list[str]]:
    """Extract novelWriter and Arcanum metadata tags in a single linear pass."""
    tags: dict[str, list[str]] = {}
    for match in TAG_LINE_REGEX.finditer(content):
        tag_key = match.group(1).lower()
        tag_val = match.group(2).strip()
        canonical_key = TAG_KEY_MAP.get(tag_key)
        if canonical_key and tag_val:
            tags.setdefault(canonical_key, []).append(tag_val)
    return tags


def get_cache_path(project_dir: str | Path) -> Path:
    return Path(project_dir) / CACHE_FILENAME


def load_cache(project_dir: str | Path) -> dict[str, Any]:
    cache_path = get_cache_path(project_dir)
    if not cache_path.is_file():
        legacy_path = Path(project_dir) / ".scriptorium_cache.json"
        if legacy_path.is_file():
            cache_path = legacy_path
        else:
            return {"version": CACHE_VERSION, "files": {}}
    try:
        with open(cache_path, encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict) and data.get("version") == CACHE_VERSION and isinstance(data.get("files"), dict):
                return data
    except Exception as e:
        logger.debug("Failed to load or parse cache at %s: %s", cache_path, e)
    return {"version": CACHE_VERSION, "files": {}}


def save_cache(project_dir: str | Path, cache_data: dict[str, Any]) -> bool:
    cache_path = get_cache_path(project_dir)
    try:
        content = json.dumps(cache_data, indent=2, ensure_ascii=False)
        atomic_write(cache_path, content)
        return True
    except Exception as e:
        logger.error("Failed to save cache to %s: %s", cache_path, e)
        return False


def parse_frontmatter(content: str) -> dict[str, Any]:
    """Parses frontmatter block delegating to the unified frontmatter engine."""
    return parse_yaml_frontmatter(content)


def parse_markdown_file(file_path: Path) -> dict[str, Any]:
    truncated = False
    try:
        stat = file_path.stat()
        mtime = stat.st_mtime
        size = stat.st_size
        with open(file_path, "rb") as fh:
            data = fh.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            truncated = True
            data = data[:MAX_BYTES]
        content = data.decode("utf-8", errors="replace")

        words = count_words(content)
        tags = extract_tags(content)
        raw_links = [m.rstrip("\\").strip() for m in WIKILINK_REGEX.findall(content)]
        wikilinks = sorted({k for k in raw_links if k})
        frontmatter = parse_frontmatter(content)

        entry: dict[str, Any] = {
            "mtime": mtime,
            "size": size,
            "word_count": words,
            "tags": tags,
            "wikilinks": wikilinks,
            "frontmatter": frontmatter,
        }
        if truncated:
            entry["truncated"] = True
            entry["error"] = f"file exceeds {MAX_BYTES // (1024 * 1024)} MiB read cap; content truncated"
        return entry
    except Exception as e:
        logger.warning("Error reading or parsing markdown file %s: %s", file_path, e)
        return {
            "mtime": 0,
            "size": 0,
            "word_count": 0,
            "tags": {},
            "wikilinks": [],
            "frontmatter": {},
            "error": str(e),
        }


def scan_project(project_dir: str | Path, force: bool = False) -> dict[str, Any]:
    pdir = Path(project_dir).resolve()
    if not pdir.is_dir():
        return {"version": CACHE_VERSION, "files": {}}
    cache = {"version": CACHE_VERSION, "files": {}} if force else load_cache(str(pdir))
    files_raw = cache.get("files")
    files_cache: dict[str, Any] = files_raw if isinstance(files_raw, dict) else {}
    updated = False

    current_files = set()
    errors = 0
    for md_path in pdir.rglob("*.md"):
        if ".obsidian" in md_path.parts or ".git" in md_path.parts or md_path.name.startswith("."):
            continue
        if any(part in EXCLUDE_DIR_NAMES for part in md_path.parts):
            continue
        rel_path = str(md_path.relative_to(pdir)).replace("\\", "/")
        current_files.add(rel_path)

        try:
            stat = md_path.stat()
            cached_entry = files_cache.get(rel_path)
            if (
                not cached_entry
                or cached_entry.get("mtime") != stat.st_mtime
                or cached_entry.get("size") != stat.st_size
            ):
                parsed = parse_markdown_file(md_path)
                files_cache[rel_path] = parsed
                if parsed.get("error"):
                    errors += 1
                updated = True
            elif cached_entry.get("error"):
                errors += 1
        except Exception as e:
            logger.warning("Failed to inspect %s: %s", md_path, e)
            errors += 1
            continue

    stale_keys = [k for k in files_cache if k not in current_files]
    if stale_keys:
        for k in stale_keys:
            del files_cache[k]
        updated = True

    cache["files"] = files_cache
    cache["errors"] = errors
    cache["healthy"] = errors == 0
    if updated or force or not get_cache_path(str(pdir)).exists():
        save_cache(str(pdir), cache)

    return cache


def compute_wordcounts(project_dir: str | Path, include_pov: bool = False) -> dict[str, Any]:
    cache = scan_project(project_dir)
    total_words = 0
    by_folder: dict[str, int] = {}
    pov_dist: dict[str, int] = {}

    for rel_path, data in cache.get("files", {}).items():
        wc = data.get("word_count", 0)
        total_words += wc
        folder = os.path.dirname(rel_path) or "(root)"
        by_folder[folder] = by_folder.get(folder, 0) + wc

        pov = (
            data.get("tags", {}).get("pov")
            or data.get("frontmatter", {}).get("pov")
            or "Unspecified"
        )
        if isinstance(pov, list):
            pov = pov[0] if pov else "Unspecified"
        pov = str(pov).strip()
        pov_dist[pov] = pov_dist.get(pov, 0) + wc

    file_count = len(cache.get("files", {}))
    res: dict[str, Any] = {
        "project": os.path.basename(str(project_dir)),
        "total_words": total_words,
        "total_files": file_count,
        "chapter_count": file_count,
        "by_folder": by_folder,
    }
    if include_pov:
        res["pov_distribution"] = pov_dist
    return res


# =============================================================================
# Centralized Data Access Layer (DAL)
# =============================================================================


@dataclass
class _CachedFileEntry:
    mtime: float
    size: int
    content: str
    frontmatter: dict[str, Any]
    body: str
    word_count: int = 0


class DataAccessLayer:
    """Thread-safe cached data access layer for Ars Arcanum repositories with LRU bounds."""

    def __init__(self, max_entries: int = 500) -> None:
        self._lock = threading.RLock()
        self._file_cache: OrderedDict[str, _CachedFileEntry] = OrderedDict()
        self.max_entries = max_entries
        self._hits = 0
        self._misses = 0

    def clear(self) -> None:
        """Clears all cached file and frontmatter entries."""
        with self._lock:
            self._file_cache.clear()
            self._hits = 0
            self._misses = 0

    def evict(self, target: Path | str) -> int:
        """Evicts a specific file path or all files under a directory prefix from cache."""
        p = Path(target).resolve()
        path_str = str(p)
        evicted = 0

        with self._lock:
            if path_str in self._file_cache:
                del self._file_cache[path_str]
                return 1

            keys_to_delete = []
            for k in list(self._file_cache.keys()):
                kp = Path(k)
                if kp == p:
                    keys_to_delete.append(k)
                else:
                    try:
                        if kp.is_relative_to(p):
                            keys_to_delete.append(k)
                    except AttributeError:
                        if k.startswith(path_str):
                            keys_to_delete.append(k)

            for k in keys_to_delete:
                del self._file_cache[k]
                evicted += 1

        return evicted

    def get_stats(self) -> dict[str, int]:
        """Returns cache telemetry statistics."""
        with self._lock:
            return {
                "cached_files": len(self._file_cache),
                "max_entries": self.max_entries,
                "cache_hits": self._hits,
                "cache_misses": self._misses,
            }

    def read_file(self, file_path: Path | str) -> str:
        """Reads text content of a file using thread-safe mtime caching with LRU promotion."""
        p = Path(file_path).resolve()
        if not p.is_file():
            return ""

        try:
            stat = p.stat()
            mtime = stat.st_mtime
            size = stat.st_size
        except OSError:
            return ""

        path_key = str(p)
        with self._lock:
            cached = self._file_cache.get(path_key)
            if cached is not None and cached.mtime == mtime and cached.size == size:
                self._hits += 1
                self._file_cache.move_to_end(path_key)
                return cached.content

        try:
            content = p.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            logger.warning("Failed reading file %s: %s", p, e)
            return ""

        frontmatter, body = extract_frontmatter_and_body(content)
        w_count = count_prose_words(content)

        with self._lock:
            self._misses += 1
            if path_key in self._file_cache:
                self._file_cache.move_to_end(path_key)
            self._file_cache[path_key] = _CachedFileEntry(
                mtime=mtime,
                size=size,
                content=content,
                frontmatter=frontmatter,
                body=body,
                word_count=w_count,
            )
            while len(self._file_cache) > self.max_entries:
                self._file_cache.popitem(last=False)

        return content

    def parse_frontmatter(self, file_path: Path | str) -> tuple[dict[str, Any], str]:
        """Returns cached (frontmatter_dict, body_text) tuple for a markdown file."""
        p = Path(file_path).resolve()
        path_key = str(p)

        content = self.read_file(p)
        if not content:
            return {}, ""

        with self._lock:
            cached = self._file_cache.get(path_key)
            if cached is not None:
                return dict(cached.frontmatter), cached.body

        frontmatter, body = extract_frontmatter_and_body(content)
        return frontmatter, body

    parse_frontmatter_and_body = parse_frontmatter

    def read_manifest(self, manifest_path: Path | str) -> dict[str, Any]:
        """Reads and parses a YAML/JSON manifest file (e.g. manuscript.yaml, world.yaml) using cache."""
        p = Path(manifest_path).resolve()
        content = self.read_file(p)
        if not content:
            return {}
        try:
            res = parse_yaml_document(content)
            return res if isinstance(res, dict) else {}
        except Exception as e:
            logger.debug("Failed parsing manifest at %s: %s", p, e)
            return {}

    def get_word_count(self, file_path: Path | str) -> int:
        """Returns cached canonical prose word count for a file."""
        p = Path(file_path).resolve()
        path_key = str(p)
        self.read_file(p)
        with self._lock:
            cached = self._file_cache.get(path_key)
            if cached is not None:
                return cached.word_count
        return 0

    def list_files(
        self,
        directory: Path | str,
        extensions: tuple[str, ...] = (".md", ".markdown"),
        recursive: bool = True,
    ) -> list[Path]:
        """Lists files matching extensions under directory, sorted by path."""
        p = Path(directory).resolve()
        if not p.is_dir():
            return []

        results: list[Path] = []
        iterator = p.rglob("*") if recursive else p.glob("*")
        for f in iterator:
            if f.is_file() and not f.name.startswith((".", "_")) and f.suffix.lower() in extensions:
                results.append(f)

        return sorted(results)

    def get_manuscript_chapters(self, manuscript_dir: Path | str) -> list[dict[str, Any]]:
        """Extracts structured chapter descriptors from a manuscript directory with canonical word counting."""
        p = Path(manuscript_dir).resolve()
        if not p.is_dir():
            return []

        chapters: list[dict[str, Any]] = []
        files = self.list_files(p)

        for f in files:
            if "outlines" in f.parts or "back_matter" in str(f).lower():
                continue
            content = self.read_file(f)
            prose_words = count_prose_words(content)
            raw_words = len(content.split())
            fm, _ = self.parse_frontmatter(f)
            title = fm.get("title", f.stem.replace("_", " ").replace("-", " "))
            chapters.append({
                "path": str(f),
                "file": f.name,
                "title": title,
                "words": prose_words,
                "prose_words": prose_words,
                "raw_words": raw_words,
                "frontmatter": fm,
            })

        return chapters

    def get_lore_entities(self, world_dir: Path | str) -> list[dict[str, Any]]:
        """Extracts lore entities categorized by sub-directory under a World Bible."""
        p = Path(world_dir).resolve()
        if not p.is_dir():
            return []

        entities: list[dict[str, Any]] = []
        files = self.list_files(p)

        for f in files:
            rel = f.relative_to(p)
            category = rel.parts[0] if len(rel.parts) > 1 else "Root"
            if category.startswith("."):
                continue

            fm, _body = self.parse_frontmatter(f)
            name = fm.get("name", f.stem.replace("_", " "))
            tags = fm.get("tags", [])
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",") if t.strip()]

            entities.append({
                "path": str(f),
                "file": f.name,
                "name": name,
                "category": category,
                "tags": tags,
                "frontmatter": fm,
            })

        return entities


_GLOBAL_DAL: DataAccessLayer | None = None


def get_data_access() -> DataAccessLayer:
    """Returns the global shared DataAccessLayer singleton instance."""
    global _GLOBAL_DAL
    if _GLOBAL_DAL is None:
        _GLOBAL_DAL = DataAccessLayer()
    return _GLOBAL_DAL


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for cache operations."""
    parser = argparse.ArgumentParser(description="Ars Arcanum Fast Cache Engine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_cmd = subparsers.add_parser("scan", help="Scan and update project cache")
    scan_cmd.add_argument("path", help="Project directory path")
    scan_cmd.add_argument("--force", action="store_true", help="Force full rescan")

    wc_cmd = subparsers.add_parser("wordcounts", help="Get aggregated word counts")
    wc_cmd.add_argument("path", help="Project directory path")
    wc_cmd.add_argument("--json", action="store_true", help="Output JSON format")
    wc_cmd.add_argument("--md", "--markdown", dest="markdown", action="store_true", help="Output Markdown table format")
    wc_cmd.add_argument("--pov", action="store_true", help="Include POV distribution metrics")

    clear_cmd = subparsers.add_parser("clear", help="Clear cache file")
    clear_cmd.add_argument("path", help="Project directory path")

    args = parser.parse_args(argv)

    if args.command == "scan":
        res = scan_project(args.path, force=args.force)
        count = len(res.get("files", {}))
        print(f"[CACHE] Indexed {count} Markdown files in {args.path}")
        if argv is None:
            sys.exit(0)
        return 0

    if args.command == "wordcounts":
        res = compute_wordcounts(args.path, include_pov=getattr(args, "pov", False))
        if args.json:
            print(json.dumps(res, indent=2))
        elif args.markdown:
            print(f"# Wordcount Report: {res['project']}\n")
            print(f"**Total Word Count**: {res['total_words']:,} words across {res['total_files']} files\n")
            print("| Section / Folder | Word Count |")
            print("| :--- | :--- |")
            for folder, count_val in sorted(res["by_folder"].items()):
                print(f"| `{folder}` | {count_val:,} |")
        else:
            print(f"Project: {res['project']}")
            print(f"Total Word Count: {res['total_words']:,} words across {res['total_files']} files\n")
            print("Breakdown by folder:")
            for folder, count_val in sorted(res["by_folder"].items()):
                print(f"  - {folder}: {count_val:,} words")
        if argv is None:
            sys.exit(0)
        return 0

    if args.command == "clear":
        cp = get_cache_path(args.path)
        legacy_cp = Path(args.path) / ".scriptorium_cache.json"
        cleared = False
        if cp.exists():
            cp.unlink()
            print(f"[CACHE] Cleared {cp}")
            cleared = True
        if legacy_cp.exists():
            legacy_cp.unlink()
            print(f"[CACHE] Cleared {legacy_cp}")
            cleared = True
        if not cleared:
            print(f"[CACHE] No cache found at {cp}")
        if argv is None:
            sys.exit(0)
        return 0

    return 0


__all__ = [
    "CACHE_FILENAME",
    "CACHE_VERSION",
    "DataAccessLayer",
    "EXCLUDE_DIR_NAMES",
    "FENCED_CODE_REGEX",
    "FRONTMATTER_REGEX",
    "MAX_BYTES",
    "NW_TAG_LINE_REGEX",
    "TAG_KEY_MAP",
    "TAG_LINE_REGEX",
    "TAG_REGEXES",
    "WIKILINK_REGEX",
    "WORD_REGEX",
    "compute_wordcounts",
    "count_prose_words",
    "count_words",
    "extract_tags",
    "get_cache_path",
    "get_data_access",
    "load_cache",
    "main",
    "parse_frontmatter",
    "parse_markdown_file",
    "save_cache",
    "scan_project",
]


if __name__ == "__main__":
    main()
