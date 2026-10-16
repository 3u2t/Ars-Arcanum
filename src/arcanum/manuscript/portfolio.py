"""Ars Arcanum Portfolio Dashboard & Catalog Analytics Engine (src/arcanum/manuscript/portfolio.py).

Zero-dependency, offline author portfolio dashboard and catalog analytics engine.
Integrates manuscript word counts, editorial lifecycle stages, lore codex metrics,
sprint telemetry, and portfolio velocity forecasting.
"""

from __future__ import annotations

import argparse
import datetime
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any

from src.arcanum.core.frontmatter import (
    extract_frontmatter_and_body,
    parse_yaml_document,
)
from src.arcanum.core.scope import (
    add_scope_arguments,
    parse_scope_args,
    resolve_manuscript_dir,
)

logger = logging.getLogger("arcanum.manuscript.portfolio")

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Canonical Prose Word Counter Regex Patterns
_FRONTMATTER_PATTERN = re.compile(r"^---\s*\r?\n(.*?)\r?\n---\s*(?:\r?\n|$)", re.DOTALL)
_FENCED_CODE_PATTERN = re.compile(r"```[\s\S]*?```", re.DOTALL)
_HTML_COMMENT_PATTERN = re.compile(r"<!--[\s\S]*?-->", re.DOTALL)
_NW_TAG_LINE_PATTERN = re.compile(r"^@[A-Za-z0-9_-]+:", re.MULTILINE)
_WORD_PATTERN = re.compile(r"\b\w+\b", re.UNICODE)


def count_prose_words(text: str) -> int:
    """Canonical Unicode-aware prose word counter across all Ars Arcanum engines."""
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


LORE_CATEGORIES = [
    "Characters",
    "Locations",
    "Factions",
    "Magic-Technology",
    "MagicSystems",
    "Cosmology",
    "History",
    "Economies",
    "Languages",
    "Bestiary",
    "Artifacts",
]


def _get_dal() -> Any:
    """Returns DataAccessLayer instance if available, otherwise None."""
    try:
        from scripts.lib.data_access import get_data_access
        return get_data_access()
    except ImportError:
        try:
            from lib.data_access import get_data_access
            return get_data_access()
        except ImportError:
            return None


def _read_file_text(path: Path) -> str:
    """Reads file text safely using DAL if available, falling back to Path.read_text."""
    dal = _get_dal()
    if dal:
        try:
            return str(dal.read_file(path))
        except Exception:
            pass
    return path.read_text(encoding="utf-8", errors="replace")


def _parse_yaml_doc(raw_text: str) -> dict[str, Any]:
    """Parses simple YAML document or frontmatter dictionary safely."""
    try:
        res = parse_yaml_document(raw_text)
        if isinstance(res, dict):
            return res
    except Exception:
        pass
    # Basic standard library fallback parser for key: value
    result: dict[str, Any] = {}
    for line in raw_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            val = v.strip().strip("'\"")
            if val.lower() == "true":
                result[k.strip()] = True
            elif val.lower() == "false":
                result[k.strip()] = False
            elif val.isdigit():
                result[k.strip()] = int(val)
            else:
                result[k.strip()] = val
    return result


def _resolve_draft_dir(parent_dir: Path, requested_draft: str | None = None) -> Path:
    """Finds the active or requested draft directory in a volume or manuscript directory."""
    draft_dirs = sorted([d for d in parent_dir.glob("Draft-*") if d.is_dir()])
    if not draft_dirs:
        return parent_dir
    if requested_draft:
        match = [d for d in draft_dirs if d.name.lower() == str(requested_draft).lower()]
        if match:
            return match[0]
    return draft_dirs[-1]


def analyze_manuscript_project(ms_dir: Path) -> dict[str, Any]:
    """Analyzes a single manuscript directory for stats, stage, chapters, and word counts."""
    manifest_path = ms_dir / "manuscript.yaml"
    meta: dict[str, Any] = {}
    if manifest_path.is_file():
        try:
            raw_text = _read_file_text(manifest_path)
            raw_meta = _parse_yaml_doc(raw_text)
            if isinstance(raw_meta, dict):
                meta = {str(k).lower(): v for k, v in raw_meta.items()}
        except Exception:
            meta = {}

    title = str(meta.get("title") or ms_dir.name.replace("_", " ").replace("-", " "))
    author = str(meta.get("author") or "Author")
    series = str(meta.get("series") or meta.get("universe") or "")
    volume_index = meta.get("volume_index") or meta.get("volume") or None
    target_words = int(meta.get("target_words", 80000))
    active_draft_name = meta.get("active_draft")
    explicit_stage = meta.get("stage") or meta.get("status") or None
    deadline_str = str(meta.get("deadline", "")).strip()

    target_ms_dir = ms_dir / "01-Manuscript" if (ms_dir / "01-Manuscript").is_dir() else ms_dir

    # Chapters and volumes: count only from the active/latest draft per volume/manuscript
    book_dirs = sorted([d for d in target_ms_dir.glob("Book-*") if d.is_dir()])
    volumes = [d.name for d in book_dirs] if book_dirs else ["Book-01"]

    chapter_files: list[Path] = []
    if book_dirs:
        for b in book_dirs:
            search_dir = _resolve_draft_dir(b, active_draft_name)
            for f in sorted(search_dir.rglob("*.md")):
                if (
                    not f.name.startswith((".", "_"))
                    and "Backups" not in f.parts
                    and "04_Back_Matter" not in f.parts
                    and "Back_Matter" not in f.parts
                    and "Front_Matter" not in f.parts
                    and "Exports" not in f.parts
                    and ".arcanum" not in f.parts
                ):
                    chapter_files.append(f)
    else:
        search_dir = _resolve_draft_dir(target_ms_dir, active_draft_name)
        for f in sorted(search_dir.rglob("*.md")):
            if (
                not f.name.startswith((".", "_"))
                and "Backups" not in f.parts
                and "04_Back_Matter" not in f.parts
                and "Back_Matter" not in f.parts
                and "Front_Matter" not in f.parts
                and "Exports" not in f.parts
                and ".arcanum" not in f.parts
            ):
                chapter_files.append(f)

    total_words = 0
    chapters_detail: list[dict[str, Any]] = []
    for cf in chapter_files:
        try:
            txt = _read_file_text(cf)
            w = count_prose_words(txt)
            total_words += w
            chapters_detail.append({
                "name": cf.stem.replace("_", " "),
                "filename": cf.name,
                "words": w,
                "path": str(cf),
            })
        except Exception:
            pass

    progress_pct = round((total_words / target_words * 100), 1) if target_words > 0 else 0.0

    exports_dir = ms_dir / "Exports"
    export_types: list[str] = []
    if exports_dir.is_dir():
        if list(exports_dir.glob("*.pdf")):
            export_types.append("PDF")
        if list(exports_dir.glob("*.epub")):
            export_types.append("EPUB")
        if list(exports_dir.glob("*.docx")):
            export_types.append("DOCX")

    has_exports = len(export_types) > 0

    if explicit_stage:
        stage = str(explicit_stage)
    elif has_exports and progress_pct >= 90:
        stage = "Publication-Ready"
    elif total_words >= target_words:
        stage = "Revisions / Pre-Flight"
    elif total_words >= target_words * 0.5:
        stage = "Drafting (Act II/III)"
    elif total_words > 1000:
        stage = "Drafting (Act I)"
    else:
        stage = "Scaffolding"

    days_remaining: int | None = None
    daily_words_needed: int | None = None
    deadline_status = "No Deadline"
    if deadline_str:
        try:
            dl_date = datetime.date.fromisoformat(deadline_str[:10])
            today = datetime.date.today()
            delta = (dl_date - today).days
            days_remaining = delta
            words_left = max(0, target_words - total_words)
            if delta > 0:
                daily_words_needed = round(words_left / delta)
                deadline_status = "On Track" if progress_pct >= 50 else "Active"
            elif delta == 0:
                daily_words_needed = words_left
                deadline_status = "Due Today"
            else:
                daily_words_needed = words_left
                deadline_status = "Overdue"
        except Exception:
            pass

    return {
        "id": ms_dir.name,
        "title": title,
        "author": author,
        "series": series,
        "volume_index": volume_index,
        "path": str(ms_dir),
        "volumes": volumes,
        "volume_count": len(volumes),
        "chapter_count": len(chapter_files),
        "chapters": chapters_detail,
        "word_count": total_words,
        "target_words": target_words,
        "progress_pct": min(100.0, progress_pct),
        "stage": stage,
        "has_exports": has_exports,
        "export_types": export_types,
        "deadline": deadline_str or None,
        "days_remaining": days_remaining,
        "daily_words_needed": daily_words_needed,
        "deadline_status": deadline_status,
        "active_draft": active_draft_name or (_resolve_draft_dir(target_ms_dir).name if (target_ms_dir / "Draft-01").is_dir() else "Default"),
    }


def analyze_universe_project(uni_dir: Path) -> dict[str, Any]:
    """Analyzes a shared worldbuilding lore codex vault for category metrics and link health."""
    meta_path = uni_dir / "universe.yaml"
    if not meta_path.is_file():
        meta_path = uni_dir / "world.yaml"
    if not meta_path.is_file():
        meta_path = uni_dir / "constitution.yaml"

    meta: dict[str, Any] = {}
    if meta_path.is_file():
        try:
            raw_text = _read_file_text(meta_path)
            raw_meta = _parse_yaml_doc(raw_text)
            if isinstance(raw_meta, dict):
                meta = {str(k).lower(): v for k, v in raw_meta.items()}
        except Exception:
            meta = {}

    name = str(meta.get("name") or meta.get("title") or uni_dir.name.replace("_", " ").replace("-", " "))
    desc = str(meta.get("description") or "")
    status = str(meta.get("status") or "Active")

    categories_stat: dict[str, dict[str, int]] = {}
    all_note_stems: set[str] = set()
    all_links: list[str] = []
    total_lore_words = 0
    total_notes = 0

    for md_file in uni_dir.rglob("*.md"):
        if (
            md_file.name.startswith((".", "_"))
            or "Backups" in md_file.parts
            or ".obsidian" in md_file.parts
            or "Templates" in md_file.parts
            or "templates" in md_file.parts
            or "Manuscripts" in md_file.parts
            or "01-Manuscript" in md_file.parts
        ):
            continue

        all_note_stems.add(md_file.stem.lower())
        total_notes += 1

        rel_parts = md_file.relative_to(uni_dir).parts
        cat = "General"
        if len(rel_parts) > 1:
            for top_c in LORE_CATEGORIES:
                if top_c.lower() in rel_parts[0].lower():
                    cat = top_c
                    break
            if cat == "General":
                cat = rel_parts[0].replace("_", " ").replace("-", " ")

        if cat not in categories_stat:
            categories_stat[cat] = {"count": 0, "words": 0}

        try:
            txt = _read_file_text(md_file)
            w = count_prose_words(txt)
            total_lore_words += w
            categories_stat[cat]["count"] += 1
            categories_stat[cat]["words"] += w

            wikilinks = re.findall(r"\[\[([^\]|#]+)(?:\|[^\]]+)?\]\]", txt)
            for wl in wikilinks:
                target = wl.strip().lower()
                if target:
                    all_links.append(target)
        except Exception:
            pass

    broken_links = 0
    for link in all_links:
        if link not in all_note_stems:
            broken_links += 1

    link_health_pct = round(100.0 * (len(all_links) - broken_links) / max(1, len(all_links)), 1) if all_links else 100.0

    return {
        "id": uni_dir.name,
        "name": name,
        "description": desc,
        "status": status,
        "path": str(uni_dir),
        "total_notes": total_notes,
        "total_words": total_lore_words,
        "categories": categories_stat,
        "total_links": len(all_links),
        "broken_links": broken_links,
        "link_health_pct": link_health_pct,
    }


def calculate_portfolio_velocity(candidate_dirs: list[Path] | None = None) -> dict[str, Any]:
    """Synthesizes drafting velocity and habit telemetry across .arcanum/sprint_log.jsonl

    and Obsidian writing logs.
    """
    sprints: list[dict[str, Any]] = []
    seen_session_ids: set[str] = set()

    search_roots: list[Path] = []
    if candidate_dirs:
        search_roots.extend(candidate_dirs)
    search_roots.extend([Path.home() / "Manuscripts", Path.home() / "Universes", _REPO_ROOT])

    for root in search_roots:
        if not root.is_dir():
            continue
        # 1. Look for sprint logs
        for log_f in root.rglob("sprint_log.jsonl"):
            try:
                for line in log_f.read_text(encoding="utf-8", errors="replace").splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    rec = json.loads(line)
                    sid = rec.get("session_id") or f"{rec.get('timestamp')}_{rec.get('words_written')}"
                    if sid not in seen_session_ids:
                        seen_session_ids.add(sid)
                        sprints.append(rec)
            except Exception:
                pass

        # 2. Look for Obsidian Daily Writing Logs
        for f in root.rglob("*.md"):
            if "Writing-Log" in f.name or "WritingLog" in f.name:
                if "Templates" in f.parts or "templates" in f.parts:
                    continue
                try:
                    content = f.read_text(encoding="utf-8", errors="replace")
                    fm, _ = extract_frontmatter_and_body(content)

                    if fm.get("fileClass") == "WritingLog" or fm.get("type") == "daily_writing_log":
                        date_raw = str(fm.get("date", ""))
                        if not date_raw or date_raw.startswith("<%"):
                            continue
                        sid = f"obs_{f.stem}_{date_raw}"
                        if sid not in seen_session_ids:
                            seen_session_ids.add(sid)
                            words_w = int(fm.get("words_written", 0))
                            time_m = float(fm.get("writing_time_minutes", 25.0))
                            wpm_val = float(fm.get("wpm_velocity", words_w / max(0.1, time_m)))
                            sprints.append({
                                "session_id": sid,
                                "timestamp": f"{date_raw}T12:00:00",
                                "duration_min": time_m,
                                "words_written": words_w,
                                "wpm": round(wpm_val, 2),
                                "target": int(fm.get("goal") or 1000),
                            })
                except Exception:
                    pass

    # Sort chronologically
    sprints.sort(key=lambda x: str(x.get("timestamp", "")))

    total_sessions = len(sprints)
    total_words = sum(s.get("words_written", 0) for s in sprints)
    total_minutes = sum(s.get("duration_min", 0.0) for s in sprints)
    overall_wpm = round(total_words / max(0.1, total_minutes), 2) if total_minutes > 0 else 0.0

    now = datetime.datetime.now()
    cutoff_7d = now - datetime.timedelta(days=7)
    cutoff_30d = now - datetime.timedelta(days=30)

    words_7d, min_7d = 0, 0.0
    words_30d, min_30d = 0, 0.0
    daily_totals: dict[str, int] = {}
    active_days: set[str] = set()

    for s in sprints:
        ts_str = str(s.get("timestamp", ""))
        try:
            ts_dt = datetime.datetime.fromisoformat(ts_str[:19])
        except (ValueError, TypeError):
            continue

        day_key = ts_dt.strftime("%Y-%m-%d")
        w = s.get("words_written", 0)
        m = s.get("duration_min", 0.0)

        daily_totals[day_key] = daily_totals.get(day_key, 0) + w
        if w > 0:
            active_days.add(day_key)

        if ts_dt >= cutoff_7d:
            words_7d += w
            min_7d += m
        if ts_dt >= cutoff_30d:
            words_30d += w
            min_30d += m

    rolling_7d_wpd = int(words_7d / 7) if total_sessions > 0 else 0
    rolling_7d_wpm = round(words_7d / max(0.1, min_7d), 2) if min_7d > 0 else 0.0
    rolling_30d_wpd = int(words_30d / 30) if total_sessions > 0 else 0
    rolling_30d_wpm = round(words_30d / max(0.1, min_30d), 2) if min_30d > 0 else 0.0

    today_dt = datetime.date.today()
    current_streak = 0
    check_day = today_dt
    if check_day.strftime("%Y-%m-%d") not in active_days:
        check_day = today_dt - datetime.timedelta(days=1)

    while check_day.strftime("%Y-%m-%d") in active_days:
        current_streak += 1
        check_day -= datetime.timedelta(days=1)

    history_14d: list[dict[str, Any]] = []
    for i in range(13, -1, -1):
        d = today_dt - datetime.timedelta(days=i)
        d_str = d.strftime("%Y-%m-%d")
        history_14d.append({
            "date": d_str,
            "label": d.strftime("%b %d"),
            "words": daily_totals.get(d_str, 0),
        })

    return {
        "total_sessions": total_sessions,
        "total_sprint_words": total_words,
        "total_minutes": round(total_minutes, 1),
        "overall_wpm": overall_wpm,
        "rolling_7d_wpd": rolling_7d_wpd,
        "rolling_7d_wpm": rolling_7d_wpm,
        "rolling_30d_wpd": rolling_30d_wpd,
        "rolling_30d_wpm": rolling_30d_wpm,
        "current_streak": current_streak,
        "history_14d": history_14d,
    }


def scan_portfolio(root_dir: Path | None = None, scope: Any = None) -> dict[str, Any]:
    """Scans all manuscripts and lore universes in the workspace or standard paths."""
    candidates: list[Path] = []
    if root_dir and root_dir.is_dir():
        candidates.append(root_dir)
    elif scope is not None and getattr(scope, "manuscript", None):
        try:
            ms_str = resolve_manuscript_dir(str(scope.manuscript), scope=scope)
            if ms_str:
                ms_p = Path(ms_str)
                if ms_p.is_dir():
                    candidates.append(ms_p)
        except Exception:
            pass

    if not candidates:
        home = Path.home()
        candidates.extend([
            home / "Manuscripts",
            home / "Universes",
            _REPO_ROOT / "templates",
            _REPO_ROOT / "templates" / "demo-cosmos",
            _REPO_ROOT / "templates" / "world-bible",
        ])

    manuscript_dirs: list[Path] = []
    universe_dirs: list[Path] = []
    seen_paths: set[Path] = set()

    for c in candidates:
        if not c.is_dir():
            continue
        c_res = c.resolve()
        if c_res in seen_paths:
            continue

        is_ms = (c / "manuscript.yaml").is_file() or (c / "Book-01").is_dir() or any(c.glob("*.nwx"))
        is_uni = (c / "universe.yaml").is_file() or (c / "world.yaml").is_file() or (c / "constitution.yaml").is_file()

        if is_ms and c_res not in seen_paths:
            manuscript_dirs.append(c)
            seen_paths.add(c_res)
        elif is_uni and c_res not in seen_paths:
            universe_dirs.append(c)
            seen_paths.add(c_res)

        for sub in sorted(c.iterdir()):
            if not sub.is_dir() or sub.name.startswith((".", "_")):
                continue
            sub_res = sub.resolve()
            if sub_res in seen_paths:
                continue

            sub_is_ms = (sub / "manuscript.yaml").is_file() or (sub / "Book-01").is_dir() or any(sub.glob("*.nwx"))
            sub_is_uni = (sub / "universe.yaml").is_file() or (sub / "world.yaml").is_file() or (sub / "constitution.yaml").is_file()

            if sub_is_ms:
                manuscript_dirs.append(sub)
                seen_paths.add(sub_res)
            elif sub_is_uni:
                universe_dirs.append(sub)
                seen_paths.add(sub_res)
            else:
                for subsub in sorted(sub.iterdir()):
                    if not subsub.is_dir() or subsub.name.startswith((".", "_")):
                        continue
                    ss_res = subsub.resolve()
                    if ss_res in seen_paths:
                        continue
                    if (subsub / "manuscript.yaml").is_file() or (subsub / "Book-01").is_dir() or any(subsub.glob("*.nwx")):
                        manuscript_dirs.append(subsub)
                        seen_paths.add(ss_res)
                    elif (subsub / "universe.yaml").is_file() or (subsub / "world.yaml").is_file():
                        universe_dirs.append(subsub)
                        seen_paths.add(ss_res)

    projects = [analyze_manuscript_project(d) for d in manuscript_dirs]
    universes = [analyze_universe_project(u) for u in universe_dirs]

    total_words = sum(p["word_count"] for p in projects)
    total_chapters = sum(p["chapter_count"] for p in projects)
    total_volumes = sum(p["volume_count"] for p in projects)
    total_target_words = sum(p.get("target_words", 0) for p in projects)
    overall_progress_pct = round((total_words / total_target_words * 100), 1) if total_target_words > 0 else 0.0

    total_lore_words = sum(u["total_words"] for u in universes)
    total_lore_notes = sum(u["total_notes"] for u in universes)

    velocity = calculate_portfolio_velocity(candidates + manuscript_dirs + universe_dirs)

    series_map: dict[str, list[dict[str, Any]]] = {}
    for p in projects:
        s_name = p.get("series") or "Standalones"
        if s_name not in series_map:
            series_map[s_name] = []
        series_map[s_name].append(p)

    return {
        "scan_time": datetime.datetime.now().isoformat(),
        "total_projects": len(projects),
        "total_words": total_words,
        "total_lore_words": total_lore_words,
        "total_lore_notes": total_lore_notes,
        "total_target_words": total_target_words,
        "overall_progress_pct": min(100.0, overall_progress_pct),
        "total_chapters": total_chapters,
        "total_volumes": total_volumes,
        "total_universes": len(universes),
        "projects": projects,
        "universes": universes,
        "series": series_map,
        "velocity": velocity,
    }


def generate_portfolio_html(report: dict[str, Any], output_path: Path | str) -> Path:
    """Generates the sovereign, interactive offline HTML5 Portfolio Hub."""
    try:
        from scripts.lib.portfolio_template import render_portfolio_html
        return Path(render_portfolio_html(report, output_path))
    except ImportError:
        from lib.portfolio_template import render_portfolio_html  # type: ignore[no-redef]
        return Path(render_portfolio_html(report, output_path))


def format_portfolio_terminal(report: dict[str, Any], show_tree: bool = False) -> str:
    """Formats a rich terminal visual tree and KPI summary for CLI output."""
    lines: list[str] = []
    header_bar = "═" * 78
    lines.append(header_bar)
    lines.append("=== Ars Arcanum Author Portfolio Dashboard ===")
    lines.append(header_bar)

    vel = report.get("velocity", {})
    streak = vel.get("current_streak", 0)
    w_7d = vel.get("rolling_7d_wpd", 0)
    wpm_7d = vel.get("rolling_7d_wpm", 0.0)

    lines.append(
        f" Catalog Words: {report['total_words']:,} / {report['total_target_words']:,} ({report['overall_progress_pct']}%) "
        f"| Manuscripts: {report['total_projects']} | Universes: {report.get('total_universes', 0)}"
    )
    lines.append(
        f" 7-Day Velocity: {w_7d:,} words/day ({wpm_7d} WPM) | Active Streak: {streak} day(s) 🔥"
    )
    lines.append("─" * 78)

    if show_tree and report.get("series"):
        lines.append("\n📁 Series & Franchise Hierarchy:")
        for s_name, projs in report["series"].items():
            lines.append(f"  └── 📚 {s_name}")
            for p in projs:
                p_bar_len = 15
                filled = int(p_bar_len * (p['progress_pct'] / 100.0))
                p_bar = "█" * filled + "░" * (p_bar_len - filled)
                lines.append(
                    f"      ├── 📖 {p['title']:<22} [{p_bar}] {p['progress_pct']:>5.1f}% | {p['stage']:<16} ({p['word_count']:,} w)"
                )
    else:
        lines.append("📖 Active Manuscripts:")
        for p in report["projects"]:
            p_bar_len = 12
            filled = int(p_bar_len * (p['progress_pct'] / 100.0))
            p_bar = "█" * filled + "░" * (p_bar_len - filled)
            dl_tag = f"⏰ {p['days_remaining']}d left" if p.get("days_remaining") is not None else ""
            lines.append(
                f"  • {p['title']:<22} [{p_bar}] {p['progress_pct']:>5.1f}% | {p['stage']:<18} | {p['word_count']:>6,} w {dl_tag}"
            )

    if report.get("universes"):
        lines.append("\n🪐 Shared Lore Universes & Codices:")
        for u in report["universes"]:
            lines.append(
                f"  • {u['name']:<22} | {u['total_notes']} notes | {u['total_words']:,} lore words | Link Health: {u['link_health_pct']}%"
            )

    lines.append("═" * 78)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ars Arcanum Portfolio Dashboard (OPS-103)")
    parser.add_argument("path", nargs="?", help="Optional root path to scan for manuscripts and lore universes")
    parser.add_argument("--html", help="Generate interactive HTML portfolio hub to output path")
    parser.add_argument("--open", action="store_true", help="Open generated HTML portfolio in default browser")
    parser.add_argument("--json", action="store_true", help="Output JSON results")
    parser.add_argument("--tree", action="store_true", help="Display hierarchical series tree in terminal")

    try:
        add_scope_arguments(parser, include_manuscript=False, include_world=False, target_pos_arg=False)
    except Exception:
        pass

    args = parser.parse_args(argv)

    scope = None
    try:
        scope = parse_scope_args(args)
    except Exception:
        pass

    root_p = Path(args.path) if args.path else None
    report = scan_portfolio(root_p, scope=scope)

    if args.json:
        print(json.dumps(report, indent=2))
        return 0

    print(format_portfolio_terminal(report, show_tree=args.tree))

    if args.html or args.open:
        out_p = Path(args.html) if args.html else Path("dist/portfolio_studio.html")
        generate_portfolio_html(report, out_p)
        print(f"\n✨ Interactive HTML Portfolio Studio written to: {out_p}")
        if args.open:
            import webbrowser
            try:
                webbrowser.open(out_p.resolve().as_uri())
            except Exception as exc:
                print(f"Warning: Could not open browser: {exc}", file=sys.stderr)

    return 0


__all__ = [
    "LORE_CATEGORIES",
    "analyze_manuscript_project",
    "analyze_universe_project",
    "calculate_portfolio_velocity",
    "format_portfolio_terminal",
    "generate_portfolio_html",
    "main",
    "scan_portfolio",
]
