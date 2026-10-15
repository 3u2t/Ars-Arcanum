"""Shared Hierarchical Paragraph-Hash Diff Engine & Hardlink Draft Promotion (Phase 2A Refactor).

Eliminates duplicated $O(N^2)$ diff pipelines across `scripts/lib/manuscript_diff.py` and
`scripts/lib/revision_heatmap.py`, and replaces slow recursive directory copies in
`scripts/lib/draft_manager.py` with $O(1)$ OS hardlink snapshots (`os.link` with copy fallback).

Repository Target: `scripts/lib/diff_core.py`
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import re
import shutil
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from lib.vault_index import PathSecurityError, atomic_write, is_safe_subpath, parse_frontmatter
except ImportError:
    from vault_index import PathSecurityError, atomic_write, is_safe_subpath, parse_frontmatter

_WORD_RE = re.compile(r"[A-Za-z0-9]+(?:['’\-][A-Za-z0-9]+)*")
_NOVELWRITER_TAG_RE = re.compile(r"^\s*@[a-zA-Z0-9_]+\s*:.*$", re.MULTILINE)


@dataclass(frozen=True)
class ParagraphDelta:
    """Word-level delta for a single added, deleted, or modified paragraph."""

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


def _split_clean_paragraphs(markdown_text: str) -> list[str]:
    """Strip YAML frontmatter and `@pov:` directives, then split into clean paragraphs."""
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
    """Branch `parent_draft_name` into `new_draft_name` using OS hardlinks (`os.link`)."""
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
            try:
                os.link(src_file, dst_file)
            except OSError:
                shutil.copy2(src_file, dst_file)
            linked_files += 1

    stamp = datetime.now(timezone.utc).isoformat()
    lineage_meta = {
        "draft": new_draft_name,
        "parent_draft": parent_draft_name,
        "milestone": milestone_tag,
        "created_at": stamp,
        "hardlinked_files": linked_files,
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
