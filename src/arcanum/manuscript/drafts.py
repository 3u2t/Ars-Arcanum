"""Ars Arcanum Manuscript Draft Versioning & Lineage Manager.

Module: src/arcanum/manuscript/drafts.py
Pure-Python standard library revision lifecycle manager, granular chapter
scoping engine, milestone tracker, and immutability lock orchestrator for
novel manuscript repositories.

Engineering Contracts:
- 100% sovereign offline architecture (zero cloud telemetry, zero external pip dependencies).
- Strict path traversal defense with `is_safe_subpath`.
- Atomic writes with Windows backoff retry (`atomic_write`).
- Separation of concerns: Subsystem 1 (file safety/locks) & Subsystem 2 (advisory telemetry).
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.arcanum.core.storage import PathSecurityError, atomic_write, is_safe_subpath

from src.arcanum.core.scope import parse_number_ranges

from src.arcanum.core.frontmatter import (
    extract_frontmatter_and_body,
    parse_yaml_document,
    serialize_yaml_document,
)

logger = logging.getLogger("arcanum.manuscript.drafts")

WINDOWS_RESERVED_NAMES = frozenset({
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
})

_FRONTMATTER_PATTERN = re.compile(r"^---\s*\r?\n(.*?)\r?\n---\s*(?:\r?\n|$)", re.DOTALL)
_FENCED_CODE_PATTERN = re.compile(r"```[\s\S]*?```", re.DOTALL)
_HTML_COMMENT_PATTERN = re.compile(r"<!--[\s\S]*?-->", re.DOTALL)
_NW_TAG_LINE_PATTERN = re.compile(r"^@[A-Za-z0-9_-]+:", re.MULTILINE)
_WORD_PATTERN = re.compile(r"\b\w+\b", re.UNICODE)


def count_prose_words(text: str) -> int:
    """Canonical, Unicode-aware prose word counter across all Ars Arcanum engines."""
    if not text:
        return 0
    clean = _FRONTMATTER_PATTERN.sub("", text)
    clean = _FENCED_CODE_PATTERN.sub("", clean)
    clean = _HTML_COMMENT_PATTERN.sub("", clean)
    lines: list[str] = []
    for ln in clean.splitlines():
        s = ln.strip()
        if not s:
            continue
        if s.startswith("@") and _NW_TAG_LINE_PATTERN.match(s):
            continue
        if s.startswith("%"):
            continue
        lines.append(ln)
    return len(_WORD_PATTERN.findall("\n".join(lines)))


def sanitize_identifier(name: str, fallback: str = "item") -> str:
    """Sanitize a name to a safe filesystem identifier token [A-Za-z0-9_-]."""
    if not name:
        return fallback

    base = str(name).split(".")[0].upper()
    if base in WINDOWS_RESERVED_NAMES:
        return fallback

    safe = re.sub(r"[^A-Za-z0-9_-]", "", str(name))
    if not safe or safe.split(".")[0].upper() in WINDOWS_RESERVED_NAMES or safe.upper() in WINDOWS_RESERVED_NAMES:
        return fallback
    return safe


def validate_volume_name(vol: str) -> str:
    """Validate volume identifier against path traversal and forbidden characters."""
    if not vol:
        raise ValueError("Volume name cannot be empty.")
    if vol in ("all", "ALL", "all-books", "omnibus"):
        return vol
    if ".." in vol or "/" in vol or "\\" in vol:
        raise ValueError(f"Invalid volume name '{vol}': path traversal characters ('..', '/', '\\') are not allowed.")
    if not re.match(r"^[A-Za-z0-9_-]+$", vol):
        raise ValueError(f"Invalid volume name '{vol}': only alphanumeric characters, hyphens, and underscores allowed.")
    base_name = vol.split(".")[0].upper()
    if base_name in WINDOWS_RESERVED_NAMES:
        raise ValueError(f"Invalid volume name '{vol}': Windows reserved device name not allowed.")
    return vol


@dataclass
class ChapterInfo:
    """Telemetry and path record for a single chapter file."""

    filename: str
    title: str
    number: int | None
    words: int
    path: str


@dataclass
class DraftInfo:
    """Metadata record for a manuscript draft version."""

    name: str
    volume: str
    path: str
    parent_draft: str | None = None
    created_at: str = ""
    is_active: bool = False
    locked: bool = False
    milestone: str = "Draft"
    notes: str = ""
    chapter_count: int = 0
    word_count: int = 0
    chapters: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _natural_path_sort_key(p: Path, base_dir: Path) -> list[tuple[int, Any]]:
    """Returns safe natural sort key for hierarchical relative paths with mixed int/str tokens."""
    try:
        rel = p.relative_to(base_dir)
    except ValueError:
        rel = p
    key: list[tuple[int, Any]] = []
    for part in rel.parts:
        tokens = re.split(r"(\d+)", part)
        for t in tokens:
            if not t:
                continue
            if t.isdigit():
                key.append((0, int(t)))
            else:
                key.append((1, t.lower()))
    return key


def _extract_chapter_number(filename: str) -> int | None:
    """Extract integer chapter number from filename like '01_Chapter_03.md' or 'ch02.md'."""
    m_ch = re.search(r"(?:chapter|ch|ep|episode)[_\s-]*(\d+)", filename, re.IGNORECASE)
    if m_ch:
        return int(m_ch.group(1))
    m = re.search(r"(\d+)", filename)
    return int(m.group(1)) if m else None


def _extract_title_from_content(path: Path, content: str) -> str:
    """Extract title from YAML frontmatter or first markdown heading (# Title)."""
    fm, body = extract_frontmatter_and_body(content)
    if fm and "title" in fm:
        return str(fm["title"])
    for line in body.splitlines():
        line_s = line.strip()
        if line_s.startswith("# "):
            return line_s[2:].strip()
        if line_s.startswith("## "):
            return line_s[3:].strip()
    return path.stem.replace("_", " ").replace("-", " ")


class DraftManager:
    """Core manager for discovering, forking, activating, and locking manuscript drafts."""

    def __init__(self, target_dir: Path | str) -> None:
        target = Path(target_dir).resolve()
        if not target.is_dir():
            raise FileNotFoundError(f"Manuscript directory not found: {target_dir}")
        self.ms_path = target
        self.manifest_path = self.ms_path / "manuscript.yaml"
        self._manifest_cache: dict[str, Any] | None = None

    def _get_active_parent(self, volume_name: str | None = None) -> Path:
        """Resolve target volume directory (Book-01) or base manuscript directory."""
        target = self.ms_path / "01-Manuscript" if (self.ms_path / "01-Manuscript").is_dir() else self.ms_path
        book_dirs = sorted([d for d in target.glob("Book-*") if d.is_dir()])
        if volume_name:
            clean_vol = sanitize_identifier(volume_name).lower()
            for b in book_dirs:
                if b.name.lower() == clean_vol or b.name.lower().endswith(clean_vol):
                    return b
            custom = target / volume_name
            if custom.is_dir():
                return custom
        return book_dirs[0] if book_dirs else target

    def _load_manifest(self, reload: bool = True) -> dict[str, Any]:
        """Load manuscript.yaml or return empty scaffold dict."""
        if not reload and self._manifest_cache is not None:
            return self._manifest_cache
        if self.manifest_path.is_file():
            try:
                data = parse_yaml_document(self.manifest_path.read_text(encoding="utf-8", errors="replace"))
                if isinstance(data, dict):
                    self._manifest_cache = data
                    return data
            except Exception as e:
                logger.warning("Could not parse manuscript manifest: %s", e)
        self._manifest_cache = {}
        return self._manifest_cache

    def _save_manifest(self, data: dict[str, Any]) -> None:
        """Atomically save manifest data back to manuscript.yaml."""
        self._manifest_cache = data
        atomic_write(self.manifest_path, serialize_yaml_document(data))

    def list_drafts(self, volume_name: str | None = None) -> list[DraftInfo]:
        """List all existing drafts with full lineage, lock, and milestone metadata."""
        manifest = self._load_manifest()
        active_draft_name = manifest.get("active_draft")
        manifest_drafts = manifest.get("drafts", {})
        if not isinstance(manifest_drafts, dict):
            manifest_drafts = {}

        target = self.ms_path / "01-Manuscript" if (self.ms_path / "01-Manuscript").is_dir() else self.ms_path
        book_dirs = sorted([d for d in target.glob("Book-*") if d.is_dir()])

        results: list[DraftInfo] = []

        def inspect_draft_dir(d_dir: Path, vol_label: str) -> DraftInfo:
            d_name = d_dir.name
            meta = manifest_drafts.get(d_name, {})
            if not isinstance(meta, dict):
                meta = {}

            # Read chapters recursively (preserving subfolder structure like Acts/Parts)
            ch_files = sorted(
                [f for f in d_dir.rglob("*.md") if not any(part.startswith((".", "_")) for part in f.relative_to(d_dir).parts)],
                key=lambda p: _natural_path_sort_key(p, d_dir),
            )
            ch_list: list[dict[str, Any]] = []
            total_words = 0
            for cf in ch_files:
                try:
                    content = cf.read_text(encoding="utf-8", errors="replace")
                    w_count = count_prose_words(content)
                    title = _extract_title_from_content(cf, content)
                    num = _extract_chapter_number(cf.name)
                    total_words += w_count
                    rel_p = str(cf.relative_to(d_dir)).replace("\\", "/")
                    ch_list.append({
                        "filename": cf.name,
                        "rel_path": rel_p,
                        "title": title,
                        "number": num,
                        "words": w_count,
                        "path": str(cf),
                    })
                except Exception as e:
                    logger.debug("Failed reading chapter %s: %s", cf, e)

            is_active = (active_draft_name and d_name.lower() == str(active_draft_name).lower()) or False
            is_locked = bool(meta.get("locked", False))
            milestone = str(meta.get("milestone", "Draft"))
            notes = str(meta.get("notes", ""))
            parent_draft = meta.get("parent_draft")
            created_at = str(meta.get("created_at", ""))

            return DraftInfo(
                name=d_name,
                volume=vol_label,
                path=str(d_dir),
                parent_draft=parent_draft,
                created_at=created_at,
                is_active=is_active,
                locked=is_locked,
                milestone=milestone,
                notes=notes,
                chapter_count=len(ch_list),
                word_count=total_words,
                chapters=ch_list,
            )

        if book_dirs:
            for b in book_dirs:
                if volume_name and b.name.lower() != volume_name.lower() and not b.name.lower().endswith(volume_name.lower()):
                    continue
                for d in sorted(b.glob("Draft-*")):
                    if d.is_dir() and "Backups" not in d.parts:
                        results.append(inspect_draft_dir(d, b.name))
        else:
            for d in sorted(target.glob("Draft-*")):
                if d.is_dir() and "Backups" not in d.parts:
                    results.append(inspect_draft_dir(d, "Root"))

        # If no active draft was explicitly set, treat the last one as active
        if results and not any(d.is_active for d in results):
            results[-1].is_active = True

        return results

    def get_draft(self, draft_name: str, volume_name: str | None = None) -> DraftInfo | None:
        """Find a specific draft by name."""
        clean_name = sanitize_identifier(draft_name).lower()
        for d in self.list_drafts(volume_name):
            if d.name.lower() == clean_name:
                return d
        return None

    def get_lineage_graph(self, volume_name: str | None = None) -> list[dict[str, Any]]:
        """Return structured lineage tree nodes connecting parents to children."""
        drafts = self.list_drafts(volume_name)
        nodes: dict[str, dict[str, Any]] = {
            d.name: {**d.to_dict(), "children": []} for d in drafts
        }

        root_nodes: list[dict[str, Any]] = []
        for d in drafts:
            parent = d.parent_draft
            if parent and parent in nodes:
                nodes[parent]["children"].append(nodes[d.name])
            else:
                root_nodes.append(nodes[d.name])

        return root_nodes

    def fork_draft(
        self,
        new_draft_name: str | None = None,
        source_draft_name: str | None = None,
        volume_name: str | None = None,
        chapters: str | int | Sequence[Any] | None = None,
        exclude: str | int | Sequence[Any] | None = None,
        milestone: str | None = "Draft",
        notes: str | None = "",
        activate: bool = True,
        reset_frontmatter: bool = False,
    ) -> dict[str, Any]:
        """Fork an existing draft into a new draft with optional granular chapter scoping."""
        active_parent = self._get_active_parent(volume_name)
        existing_drafts = sorted([d for d in active_parent.glob("Draft-*") if d.is_dir()])

        # 1. Resolve source draft
        src_draft_dir: Path | None = None
        if source_draft_name:
            clean_src = sanitize_identifier(source_draft_name).lower()
            matches = [d for d in existing_drafts if d.name.lower() == clean_src]
            if matches:
                src_draft_dir = matches[0]
            else:
                raise FileNotFoundError(f"Source draft '{source_draft_name}' not found.")
        elif existing_drafts:
            manifest = self._load_manifest()
            act_name = manifest.get("active_draft")
            if act_name:
                matches = [d for d in existing_drafts if d.name.lower() == str(act_name).lower()]
                src_draft_dir = matches[0] if matches else existing_drafts[-1]
            else:
                src_draft_dir = existing_drafts[-1]

        if volume_name and (".." in str(volume_name) or "/" in str(volume_name) or "\\" in str(volume_name)):
            raise PathSecurityError(f"Volume name contains path traversal segments: {volume_name}")

        # 2. Determine destination draft name
        if new_draft_name:
            if ".." in str(new_draft_name) or "/" in str(new_draft_name) or "\\" in str(new_draft_name):
                raise PathSecurityError(f"Draft name contains path traversal segments: {new_draft_name}")
            clean_name = sanitize_identifier(new_draft_name)
            if not clean_name.lower().startswith("draft-"):
                clean_name = f"Draft-{clean_name}"
        else:
            nums: list[int] = []
            for d in existing_drafts:
                m = re.search(r"(\d+)", d.name)
                if m:
                    nums.append(int(m.group(1)))
            next_num = (max(nums) + 1) if nums else 1
            clean_name = f"Draft-{next_num:02d}"

        dest_draft_dir = active_parent / clean_name
        if not is_safe_subpath(self.ms_path, dest_draft_dir):
            raise PathSecurityError(f"Target draft escapes manuscript root: {dest_draft_dir}")
        if dest_draft_dir.exists():
            raise FileExistsError(f"Draft directory already exists: {dest_draft_dir}")

        dest_draft_dir.mkdir(parents=True, exist_ok=True)

        # 3. Chapter scoping & copying
        copied_chapters = 0
        total_words = 0

        if src_draft_dir and src_draft_dir.is_dir():
            include_nums = set(parse_number_ranges(chapters)) if chapters else None
            exclude_nums = set(parse_number_ranges(exclude)) if exclude else set()

            src_files = sorted(
                [f for f in src_draft_dir.rglob("*.md") if not any(part.startswith((".", "_")) for part in f.relative_to(src_draft_dir).parts)],
                key=lambda p: _natural_path_sort_key(p, src_draft_dir),
            )

            for ch_idx, sf in enumerate(src_files, 1):
                ch_num = _extract_chapter_number(sf.name)
                if include_nums is not None and (ch_num not in include_nums and ch_idx not in include_nums):
                    continue
                if (ch_num is not None and ch_num in exclude_nums) or (ch_idx in exclude_nums):
                    continue

                content = sf.read_text(encoding="utf-8", errors="replace")
                if reset_frontmatter:
                    fm, body = extract_frontmatter_and_body(content)
                    if fm:
                        fm["status"] = "Draft"
                        fm.pop("revision_notes", None)
                        content = f"---\n{serialize_yaml_document(fm)}---\n\n{body.lstrip()}"

                rel_p = sf.relative_to(src_draft_dir)
                df = dest_draft_dir / rel_p
                df.parent.mkdir(parents=True, exist_ok=True)
                atomic_write(df, content)
                copied_chapters += 1
                total_words += count_prose_words(content)

        # If no chapters copied (e.g. brand new initial draft), scaffold chapter 1
        if copied_chapters == 0:
            ch_file = dest_draft_dir / "01_Chapter_01.md"
            ch_content = "---\ntitle: Chapter 1\nstatus: Draft\n---\n\n# Chapter 1\n\nBegin drafting...\n"
            atomic_write(ch_file, ch_content)
            copied_chapters = 1
            total_words = count_prose_words(ch_content)

        # 4. Update manuscript.yaml manifest
        manifest = self._load_manifest()
        if "drafts" not in manifest or not isinstance(manifest["drafts"], dict):
            manifest["drafts"] = {}

        now_iso = datetime.now(timezone.utc).isoformat()
        manifest["drafts"][clean_name] = {
            "created_at": now_iso,
            "parent_draft": src_draft_dir.name if src_draft_dir else None,
            "milestone": milestone or "Draft",
            "locked": False,
            "word_count": total_words,
            "chapter_count": copied_chapters,
            "notes": notes or "",
        }

        if activate:
            manifest["active_draft"] = clean_name

        self._save_manifest(manifest)

        return {
            "status": "success",
            "manuscript": self.ms_path.name,
            "volume": active_parent.name,
            "draft": clean_name,
            "path": str(dest_draft_dir),
            "source": src_draft_dir.name if src_draft_dir else None,
            "chapters_copied": copied_chapters,
            "word_count": total_words,
            "milestone": milestone or "Draft",
            "active": activate,
        }

    def activate_draft(self, draft_name: str, volume_name: str | None = None) -> dict[str, Any]:
        """Switch active draft in manuscript.yaml."""
        draft = self.get_draft(draft_name, volume_name)
        if not draft:
            raise FileNotFoundError(f"Draft '{draft_name}' not found.")

        manifest = self._load_manifest()
        manifest["active_draft"] = draft.name
        self._save_manifest(manifest)

        return {
            "status": "success",
            "active_draft": draft.name,
            "volume": draft.volume,
            "path": draft.path,
        }

    def lock_draft(self, draft_name: str, notes: str | None = None, volume_name: str | None = None) -> dict[str, Any]:
        """Lock a draft as immutable, protecting against accidental modifications."""
        draft = self.get_draft(draft_name, volume_name)
        if not draft:
            raise FileNotFoundError(f"Draft '{draft_name}' not found.")

        manifest = self._load_manifest()
        if "drafts" not in manifest or not isinstance(manifest["drafts"], dict):
            manifest["drafts"] = {}

        if draft.name not in manifest["drafts"]:
            manifest["drafts"][draft.name] = {
                "created_at": draft.created_at or datetime.now(timezone.utc).isoformat(),
                "parent_draft": draft.parent_draft,
                "milestone": draft.milestone,
                "locked": True,
                "word_count": draft.word_count,
                "chapter_count": draft.chapter_count,
                "notes": notes or draft.notes,
            }
        else:
            manifest["drafts"][draft.name]["locked"] = True
            if notes:
                manifest["drafts"][draft.name]["notes"] = notes

        self._save_manifest(manifest)

        lock_file = Path(draft.path) / ".locked"
        atomic_write(
            lock_file,
            f"# Sealed Immutability Lock\nlocked_at: {datetime.now(timezone.utc).isoformat()}\nnotes: {notes or ''}\n",
        )

        return {
            "status": "success",
            "draft": draft.name,
            "locked": True,
            "lock_file": str(lock_file),
            "message": f"Draft '{draft.name}' is now LOCKED and immutable.",
        }

    def unlock_draft(self, draft_name: str, force: bool = False, notes: str | None = None, volume_name: str | None = None) -> dict[str, Any]:
        """Unlock a previously locked draft."""
        draft = self.get_draft(draft_name, volume_name)
        if not draft:
            raise FileNotFoundError(f"Draft '{draft_name}' not found.")

        manifest = self._load_manifest()
        if "drafts" in manifest and isinstance(manifest["drafts"], dict) and draft.name in manifest["drafts"]:
            manifest["drafts"][draft.name]["locked"] = False
            if notes:
                manifest["drafts"][draft.name]["notes"] = notes
            self._save_manifest(manifest)

        lock_file = Path(draft.path) / ".locked"
        if lock_file.exists():
            try:
                lock_file.unlink()
            except OSError:
                pass

        return {
            "status": "success",
            "draft": draft.name,
            "locked": False,
            "message": f"Draft '{draft.name}' is now UNLOCKED and editable.",
        }

    def set_milestone(self, draft_name: str, milestone: str, volume_name: str | None = None) -> dict[str, Any]:
        """Update lifecycle milestone tag for a draft."""
        draft = self.get_draft(draft_name, volume_name)
        if not draft:
            raise FileNotFoundError(f"Draft '{draft_name}' not found.")

        manifest = self._load_manifest()
        if "drafts" not in manifest or not isinstance(manifest["drafts"], dict):
            manifest["drafts"] = {}

        if draft.name not in manifest["drafts"]:
            manifest["drafts"][draft.name] = {
                "created_at": draft.created_at or datetime.now(timezone.utc).isoformat(),
                "parent_draft": draft.parent_draft,
                "milestone": milestone,
                "locked": draft.locked,
                "word_count": draft.word_count,
                "chapter_count": draft.chapter_count,
                "notes": draft.notes,
            }
        else:
            manifest["drafts"][draft.name]["milestone"] = milestone

        self._save_manifest(manifest)

        return {
            "status": "success",
            "draft": draft.name,
            "milestone": milestone,
        }

    def set_notes(self, draft_name: str, notes: str, volume_name: str | None = None) -> dict[str, Any]:
        """Update authorial notes/changelog for a draft."""
        draft = self.get_draft(draft_name, volume_name)
        if not draft:
            raise FileNotFoundError(f"Draft '{draft_name}' not found.")

        manifest = self._load_manifest()
        if "drafts" not in manifest or not isinstance(manifest["drafts"], dict):
            manifest["drafts"] = {}

        if draft.name not in manifest["drafts"]:
            manifest["drafts"][draft.name] = {
                "created_at": draft.created_at or datetime.now(timezone.utc).isoformat(),
                "parent_draft": draft.parent_draft,
                "milestone": draft.milestone,
                "locked": draft.locked,
                "word_count": draft.word_count,
                "chapter_count": draft.chapter_count,
                "notes": notes,
            }
        else:
            manifest["drafts"][draft.name]["notes"] = notes

        self._save_manifest(manifest)

        return {
            "status": "success",
            "draft": draft.name,
            "notes": notes,
        }

    def get_draft_status(self, draft_name: str | None = None, volume_name: str | None = None) -> dict[str, Any]:
        """Return comprehensive telemetry for a draft including diff against its parent."""
        drafts = self.list_drafts(volume_name)
        if not drafts:
            raise FileNotFoundError("No drafts found in manuscript.")

        target_draft: DraftInfo | None = None
        if draft_name:
            target_draft = self.get_draft(draft_name, volume_name)
            if not target_draft:
                raise FileNotFoundError(f"Draft '{draft_name}' not found.")
        else:
            for d in drafts:
                if d.is_active:
                    target_draft = d
                    break
            if not target_draft:
                target_draft = drafts[-1]

        parent_words = None
        delta_words = None
        if target_draft.parent_draft:
            parent_d = self.get_draft(target_draft.parent_draft, volume_name)
            if parent_d:
                parent_words = parent_d.word_count
                delta_words = target_draft.word_count - parent_words

        return {
            "manuscript": self.ms_path.name,
            "volume": target_draft.volume,
            "draft": target_draft.name,
            "active": target_draft.is_active,
            "locked": target_draft.locked,
            "milestone": target_draft.milestone,
            "created_at": target_draft.created_at,
            "parent_draft": target_draft.parent_draft,
            "word_count": target_draft.word_count,
            "chapter_count": target_draft.chapter_count,
            "parent_word_count": parent_words,
            "delta_words": delta_words,
            "notes": target_draft.notes,
            "chapters": target_draft.chapters,
        }

    def render_ansi_tree(self, volume_name: str | None = None) -> str:
        """Generate a rich ANSI visual lineage tree for terminal display."""
        drafts = self.list_drafts(volume_name)
        if not drafts:
            return f"No drafts discovered for '{self.ms_path.name}'."

        manifest = self._load_manifest()
        title = manifest.get("title", self.ms_path.name)

        lines: list[str] = [
            f"🏛️  Ars Arcanum — Manuscript Draft Lineage Tree: '{title}'",
            "=" * 80,
            "",
        ]

        for idx, d in enumerate(drafts):
            is_last = idx == len(drafts) - 1
            connector = "└── " if is_last else "├── "
            active_badge = "\033[1;32m🟢 ACTIVE\033[0m" if d.is_active else "         "
            lock_badge = "\033[1;31m🔒 LOCKED\033[0m" if d.locked else "\033[1;36m🔓 EDITABLE\033[0m"
            milestone_badge = f"\033[1;33m🏷️  {d.milestone.upper()}\033[0m"

            parent_info = f" (↳ from {d.parent_draft})" if d.parent_draft else " (🌱 Genesis)"
            words_info = f"{d.word_count:,} words | {d.chapter_count} ch"

            lines.append(f"  {connector}\033[1;37m{d.name:<18}\033[0m [{d.volume}] {parent_info}")
            lines.append(f"      {active_badge}  {lock_badge}  {milestone_badge}  • {words_info}")
            if d.notes:
                lines.append(f"      \033[90mNotes: {d.notes}\033[0m")
            if not is_last:
                lines.append("  │")

        lines.append("")
        return "\n".join(lines)

    def render_html(self, output_path: Path | str | None = None, volume_name: str | None = None) -> str:
        """Generate standalone offline HTML visual dashboard."""
        try:
            from scripts.lib.draft_manager_template import generate_draft_dashboard_html
        except ImportError:
            try:
                from lib.draft_manager_template import generate_draft_dashboard_html
            except ImportError:
                from draft_manager_template import generate_draft_dashboard_html  # type: ignore[no-redef]

        manifest = self._load_manifest()
        title = manifest.get("title", self.ms_path.name)
        univ = manifest.get("universe", "")
        world = manifest.get("world", "")
        active_draft_name = manifest.get("active_draft")

        drafts = self.list_drafts(volume_name)
        drafts_data = [d.to_dict() for d in drafts]

        return generate_draft_dashboard_html(
            manuscript_title=title,
            drafts_data=drafts_data,
            active_draft_name=active_draft_name,
            universe_name=univ,
            world_name=world,
            output_path=output_path,
        )


# --- Functional API ---

def list_drafts(target_dir: Path | str, volume_name: str | None = None) -> list[dict[str, Any]]:
    """List all drafts in target manuscript directory."""
    mgr = DraftManager(target_dir)
    return [d.to_dict() for d in mgr.list_drafts(volume_name)]


def fork_draft(
    target_dir: Path | str,
    new_draft_name: str | None = None,
    source_draft_name: str | None = None,
    volume_name: str | None = None,
    chapters: str | int | Sequence[Any] | None = None,
    exclude: str | int | Sequence[Any] | None = None,
    milestone: str | None = "Draft",
    notes: str | None = "",
    activate: bool = True,
    reset_frontmatter: bool = False,
) -> dict[str, Any]:
    """Fork a draft with optional chapter slicing and milestone tagging."""
    mgr = DraftManager(target_dir)
    return mgr.fork_draft(
        new_draft_name=new_draft_name,
        source_draft_name=source_draft_name,
        volume_name=volume_name,
        chapters=chapters,
        exclude=exclude,
        milestone=milestone,
        notes=notes,
        activate=activate,
        reset_frontmatter=reset_frontmatter,
    )


def activate_draft(target_dir: Path | str, draft_name: str, volume_name: str | None = None) -> dict[str, Any]:
    """Switch active draft in manuscript manifest."""
    mgr = DraftManager(target_dir)
    return mgr.activate_draft(draft_name, volume_name)


def lock_draft(target_dir: Path | str, draft_name: str, notes: str | None = None, volume_name: str | None = None) -> dict[str, Any]:
    """Lock a draft as immutable."""
    mgr = DraftManager(target_dir)
    return mgr.lock_draft(draft_name, notes=notes, volume_name=volume_name)


def unlock_draft(target_dir: Path | str, draft_name: str, force: bool = False, notes: str | None = None, volume_name: str | None = None) -> dict[str, Any]:
    """Unlock a locked draft."""
    mgr = DraftManager(target_dir)
    return mgr.unlock_draft(draft_name, force=force, notes=notes, volume_name=volume_name)


def set_milestone(target_dir: Path | str, draft_name: str, milestone: str, volume_name: str | None = None) -> dict[str, Any]:
    """Update milestone tag for a draft."""
    mgr = DraftManager(target_dir)
    return mgr.set_milestone(draft_name, milestone=milestone, volume_name=volume_name)


def set_notes(target_dir: Path | str, draft_name: str, notes: str, volume_name: str | None = None) -> dict[str, Any]:
    """Update notes for a draft."""
    mgr = DraftManager(target_dir)
    return mgr.set_notes(draft_name, notes=notes, volume_name=volume_name)


def get_draft_status(target_dir: Path | str, draft_name: str | None = None, volume_name: str | None = None) -> dict[str, Any]:
    """Return comprehensive telemetry for a draft."""
    mgr = DraftManager(target_dir)
    return mgr.get_draft_status(draft_name=draft_name, volume_name=volume_name)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for `arcanum draft`."""
    parser = argparse.ArgumentParser(
        prog="arcanum draft",
        description="Ars Arcanum Manuscript Draft Versioning & Lineage Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("target", nargs="?", default=".", help="Manuscript name or directory (default: current directory)")
    parser.add_argument("action_or_draft", nargs="?", help="Subcommand (list, tree, fork, switch, lock, unlock, tag, status, visual) or new draft name")

    # Options & Flags
    parser.add_argument("--name", help="Draft name override")
    parser.add_argument("--source", "-s", help="Source draft to fork from (default: active/latest)")
    parser.add_argument("--chapters", "-c", help="Granular chapter numbers/ranges to import (e.g. '1-5,8')")
    parser.add_argument("--exclude", "-e", help="Chapters to exclude (e.g. '4,7')")
    parser.add_argument("--tag", "-t", "--milestone", dest="milestone", help="Milestone label (e.g. Alpha, Beta, Line-Edit)")
    parser.add_argument("--notes", "-n", help="Authorial notes or revision description")
    parser.add_argument("--no-activate", action="store_true", help="Do not switch active_draft to the new draft")
    parser.add_argument("--reset-frontmatter", action="store_true", help="Reset chapter status/notes in frontmatter")
    parser.add_argument("--volume", "-v", help="Target volume identifier (e.g. Book-01)")
    parser.add_argument("--list", "-l", action="store_true", help="List all drafts")
    parser.add_argument("--tree", action="store_true", help="Render ANSI draft lineage tree")
    parser.add_argument("--html", help="Export visual HTML dashboard to specified file path")
    parser.add_argument("--open", action="store_true", help="Open visual HTML dashboard in default browser")
    parser.add_argument("--force", "-f", action="store_true", help="Force unlock or overwrite")

    args, extra = parser.parse_known_args(argv)

    try:
        known_actions = {
            "list", "ls", "tree", "fork", "create", "new",
            "switch", "use", "activate", "lock", "unlock",
            "tag", "milestone", "status", "info", "diff",
            "visual", "dashboard",
        }

        raw_positionals = [t for t in [args.target, args.action_or_draft, *extra] if t and not t.startswith("-")]

        target_dir = "."
        subaction = "list" if args.list else None
        sub_args: list[str] = []

        if not raw_positionals:
            target_dir = "."
            subaction = "tree" if args.tree else "list"
        elif len(raw_positionals) == 1:
            tok = raw_positionals[0]
            if tok in known_actions:
                target_dir = "."
                subaction = tok
            elif tok.lower().startswith("draft-"):
                target_dir = "."
                subaction = "fork"
                sub_args = [tok]
            else:
                target_dir = tok
                subaction = "tree" if args.tree else "list"
        else:
            first = raw_positionals[0]
            second = raw_positionals[1]
            if first in known_actions:
                target_dir = "."
                subaction = first
                sub_args = raw_positionals[1:]
            elif second in known_actions:
                target_dir = first
                subaction = second
                sub_args = raw_positionals[2:]
            else:
                target_dir = first
                subaction = "fork"
                sub_args = [second, *raw_positionals[2:]]

        if args.tree:
            subaction = "tree"
        elif args.list:
            subaction = "list"

        mgr = DraftManager(target_dir)

        # 1. HTML Visual Dashboard Export
        if args.html or getattr(args, "open", False) or subaction in ("visual", "dashboard"):
            out_p = Path(args.html) if args.html else (mgr.ms_path / "drafts_dashboard.html")
            mgr.render_html(output_path=out_p, volume_name=args.volume)
            print(f"✓ Draft Manager Visual Dashboard generated: {out_p}")
            if getattr(args, "open", False):
                import webbrowser
                try:
                    webbrowser.open(out_p.resolve().as_uri())
                except Exception as exc:
                    print(f"Warning: Could not open browser: {exc}", file=sys.stderr)
            return 0

        # 2. Tree view
        if subaction == "tree":
            tree_str = mgr.render_ansi_tree(volume_name=args.volume)
            print(tree_str)
            return 0

        # 3. List view
        if subaction in ("list", "ls"):
            drafts = mgr.list_drafts(volume_name=args.volume)
            print(f"Manuscript Drafts for '{mgr.ms_path.name}' ({len(drafts)} total):")
            for d in drafts:
                act_str = " \033[32m[ACTIVE]\033[0m" if d.is_active else ""
                lock_str = " \033[31m[LOCKED]\033[0m" if d.locked else ""
                parent_str = f" (↳ {d.parent_draft})" if d.parent_draft else ""
                print(f"  • [{d.volume}] \033[1m{d.name}\033[0m{act_str}{lock_str} — {d.word_count:,} words ({d.chapter_count} ch){parent_str} [{d.milestone or 'Draft'}]")
            return 0

        # 4. Switch / Activate
        if subaction in ("switch", "use", "activate"):
            draft_target = args.name or (sub_args[0] if sub_args else None)
            if not draft_target:
                print("Error: Specify draft name to activate (e.g. 'arcanum draft switch Draft-02')", file=sys.stderr)
                return 1
            res = mgr.activate_draft(draft_target, volume_name=args.volume)
            print(f"✓ Active draft switched to: '{res['active_draft']}' [{res['volume']}]")
            return 0

        # 5. Lock
        if subaction == "lock":
            draft_target = args.name or (sub_args[0] if sub_args else None)
            if not draft_target:
                print("Error: Specify draft name to lock (e.g. 'arcanum draft lock Draft-01')", file=sys.stderr)
                return 1
            res = mgr.lock_draft(draft_target, notes=args.notes or "", volume_name=args.volume)
            print(f"🔒 {res['message']}")
            return 0

        # 6. Unlock
        if subaction == "unlock":
            draft_target = args.name or (sub_args[0] if sub_args else None)
            if not draft_target:
                print("Error: Specify draft name to unlock (e.g. 'arcanum draft unlock Draft-01')", file=sys.stderr)
                return 1
            res = mgr.unlock_draft(draft_target, force=args.force, volume_name=args.volume)
            print(f"🔓 {res['message']}")
            return 0

        # 7. Tag / Milestone
        if subaction in ("tag", "milestone"):
            draft_target = args.name or (sub_args[0] if sub_args else None)
            tag_val = sub_args[1] if len(sub_args) > 1 else (args.milestone or "Draft")
            if not draft_target or not tag_val:
                print("Error: Specify draft name and milestone (e.g. 'arcanum draft tag Draft-02 Beta')", file=sys.stderr)
                return 1
            res = mgr.set_milestone(draft_target, tag_val, volume_name=args.volume)
            print(f"🏷️  Draft '{res['draft']}' milestone set to: {res['milestone']}")
            return 0

        # 8. Status / Info
        if subaction in ("status", "info"):
            draft_target = args.name or (sub_args[0] if sub_args else None)
            stat = mgr.get_draft_status(draft_target, volume_name=args.volume)
            act_str = "🟢 Active" if stat["active"] else "Inactive"
            lock_str = "🔒 Locked" if stat["locked"] else "🔓 Editable"
            print(f"Draft Status: '{stat['draft']}' [{stat['volume']}]")
            print(f"  • State: {act_str} | {lock_str}")
            print(f"  • Milestone: {stat['milestone']}")
            print(f"  • Word Count: {stat['word_count']:,} words ({stat['chapter_count']} chapters)")
            if stat["parent_draft"]:
                delta_str = f" ({stat['delta_words']:+,} words vs parent)" if stat["delta_words"] is not None else ""
                print(f"  • Parent Draft: {stat['parent_draft']}{delta_str}")
            if stat["notes"]:
                print(f"  • Notes: {stat['notes']}")
            return 0

        # 9. Fork / Create draft
        new_d_name = args.name or (sub_args[0] if sub_args else None)
        res = mgr.fork_draft(
            new_draft_name=new_d_name,
            source_draft_name=args.source,
            volume_name=args.volume,
            chapters=args.chapters,
            exclude=args.exclude,
            milestone=args.milestone or "Draft",
            notes=args.notes or "",
            activate=not args.no_activate,
            reset_frontmatter=args.reset_frontmatter,
        )
        src_note = f" (forked from {res['source']})" if res.get("source") else ""
        print(f"✓ Created new draft: '{res['draft']}'{src_note}")
        print(f"  • Location: {res['path']}")
        print(f"  • Chapters copied: {res['chapters_copied']} ({res['word_count']:,} words)")
        print(f"  • Milestone: {res['milestone']}")
        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
