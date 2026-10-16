"""Ars Arcanum Phase Effort & Writing Velocity Engine (src/arcanum/manuscript/velocity.py).

Provides deterministic phase-weighted effort point evaluation, cognitive velocity tracking,
writing sprint state orchestration, and portfolio pipeline forecasting.

100% sovereign offline architecture, standard library only, atomic write resilient.
"""

from __future__ import annotations

import argparse
import datetime
import json
import logging
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

from src.arcanum.core.storage import PathSecurityError, atomic_write, is_safe_subpath

logger = logging.getLogger("arcanum.manuscript.velocity")

# Canonical Prose Word Counter Regex Patterns
_FRONTMATTER_PATTERN = re.compile(r"^---\s*\r?\n(.*?)\r?\n---\s*(?:\r?\n|$)", re.DOTALL)
_FENCED_CODE_PATTERN = re.compile(r"```[\s\S]*?```", re.DOTALL)
_HTML_COMMENT_PATTERN = re.compile(r"<!--[\s\S]*?-->", re.DOTALL)
_NW_TAG_LINE_PATTERN = re.compile(r"^@[A-Za-z0-9_-]+:", re.MULTILINE)
_WORD_PATTERN = re.compile(r"\b\w+\b", re.UNICODE)


def count_prose_words(text: str) -> int:
    """Canonical Unicode-aware prose word counter across all Ars Arcanum engines.

    Strips YAML frontmatter headers, fenced code blocks, HTML comments,
    Typst comment lines (%), and NovelCrafter scene directives (@tag:).
    """
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


class ProjectStage(str, Enum):
    """Canonical book lifecycle stages."""

    CONCEPT = "Concept"
    PRE_DRAFT_OUTLINE = "Pre-Draft Outline"
    DRAFTING = "Drafting"
    PRE_REVISION_OUTLINE = "Pre-Revision Outline"
    REVISION = "Revision"
    BETA_REVIEW = "Beta Review"
    PROOFING = "Proofing"
    QUERYING = "Querying"
    PUBLISHING = "Publishing"


DESIGNATED_OUTLINE_STAGES: frozenset[ProjectStage] = frozenset({
    ProjectStage.CONCEPT,
    ProjectStage.PRE_DRAFT_OUTLINE,
    ProjectStage.PRE_REVISION_OUTLINE,
})

DESIGNATED_REVISION_STAGES: frozenset[ProjectStage] = frozenset({
    ProjectStage.REVISION,
    ProjectStage.BETA_REVIEW,
    ProjectStage.PROOFING,
})


@dataclass(frozen=True)
class EffortMultiplierConfig:
    """Configurable phase-aware effort weights and career targets."""

    daily_effort_goal: float = 2_000.0
    annual_word_target: int = 730_000
    lifetime_word_milestone: int = 15_000_000
    drafting_weight: float = 1.00
    on_phase_outlining_weight: float = 1.00
    off_phase_outlining_weight: float = 0.50
    worldbuilding_weight: float = 0.50
    on_phase_revision_weight: float = 0.20
    off_phase_revision_weight: float = 0.00


@dataclass(frozen=True)
class SessionEffortBreakdown:
    """Factory-only schema stub retained for backwards compatibility."""

    session_date: str
    book_title: str
    universe: str
    series: str
    stage: ProjectStage
    worldbuilding_words: int = 0
    outlining_words: int = 0
    first_draft_words: int = 0
    revision_words: int = 0
    minutes_spent: float = 0.0
    notes: str = ""
    total_manuscript_words_added: int = field(init=False)
    total_raw_words_logged: int = field(init=False)
    effort_points: float = field(init=False)
    premature_revision_blocked: bool = field(init=False)
    words_per_hour: float = field(init=False)

    def __post_init__(self) -> None:
        raise NotImplementedError("Use `evaluate_session_effort()` factory to construct sessions.")


@dataclass(frozen=True)
class EvaluatedSession:
    """Immutable evaluated session record persisted to `.arcanum/sprint_log.jsonl`."""

    session_date: str
    book_title: str
    universe: str
    series: str
    stage: str
    worldbuilding_words: int
    outlining_words: int
    first_draft_words: int
    revision_words: int
    total_manuscript_words_added: int
    total_raw_words_logged: int
    effort_points: float
    daily_target: float
    goal_met: bool
    premature_revision_blocked: bool
    minutes_spent: float
    words_per_hour: float
    notes: str = ""


@dataclass(frozen=True)
class BookProjectSpec:
    """Metadata specification for a tracked book in the multi-year portfolio pipeline."""

    book_title: str
    universe: str
    series: str
    book_type: str
    stage: ProjectStage
    target_words: int
    start_date: str
    deadline: str
    initial_words: int = 0


@dataclass(frozen=True)
class BookPipelineTelemetry:
    """Computed live telemetry and deadline forecast for a single book project."""

    book_title: str
    universe: str
    series: str
    stage: str
    target_words: int
    actual_words: int
    progress_pct: float
    days_left: int
    required_daily_pace: int
    trailing_30d_velocity: float
    forecasted_finish_date: str
    status_label: str


@dataclass(frozen=True)
class CareerDashboardSummary:
    """Executive summary across all universes, series, and active books."""

    reference_date: str
    lifetime_career_words: int
    lifetime_milestone_pct: float
    universe_word_totals: dict[str, int]
    trailing_30d_velocity_wpd: float
    active_streak_days: int
    current_month_words: int
    monthly_word_target: int
    today_effort_points: float
    daily_effort_target: float
    daily_goal_met: bool
    book_spotlight: tuple[BookPipelineTelemetry, ...]


def evaluate_session_effort(
    *,
    session_date: str,
    book_title: str,
    universe: str = "Reliquary",
    series: str = "Standalone",
    stage: ProjectStage | str = ProjectStage.DRAFTING,
    worldbuilding_words: int = 0,
    outlining_words: int = 0,
    first_draft_words: int = 0,
    revision_words: int = 0,
    minutes_spent: float = 0.0,
    notes: str = "",
    config: EffortMultiplierConfig | None = None,
) -> EvaluatedSession:
    """Deterministically compute effort points and manuscript progress for a writing session."""
    effective_config = config or EffortMultiplierConfig()
    resolved_stage = ProjectStage(stage) if not isinstance(stage, ProjectStage) else stage

    for name, val in (
        ("worldbuilding_words", worldbuilding_words),
        ("outlining_words", outlining_words),
        ("first_draft_words", first_draft_words),
        ("revision_words", revision_words),
    ):
        if val < 0:
            raise ValueError(f"{name} must be non-negative (got {val})")

    outline_mult = (
        effective_config.on_phase_outlining_weight
        if resolved_stage in DESIGNATED_OUTLINE_STAGES
        else effective_config.off_phase_outlining_weight
    )
    in_revision_stage = resolved_stage in DESIGNATED_REVISION_STAGES
    revision_mult = (
        effective_config.on_phase_revision_weight
        if in_revision_stage
        else effective_config.off_phase_revision_weight
    )

    effort_points = round(
        (first_draft_words * effective_config.drafting_weight)
        + (outlining_words * outline_mult)
        + (worldbuilding_words * effective_config.worldbuilding_weight)
        + (revision_words * revision_mult),
        2,
    )

    manuscript_words_added = first_draft_words
    raw_words_logged = worldbuilding_words + outlining_words + first_draft_words + revision_words
    premature_revision_blocked = (revision_words > 0) and (not in_revision_stage)
    wph = round((raw_words_logged / (minutes_spent / 60.0)), 1) if minutes_spent > 0 else 0.0

    return EvaluatedSession(
        session_date=session_date,
        book_title=book_title,
        universe=universe,
        series=series,
        stage=resolved_stage.value,
        worldbuilding_words=worldbuilding_words,
        outlining_words=outlining_words,
        first_draft_words=first_draft_words,
        revision_words=revision_words,
        total_manuscript_words_added=manuscript_words_added,
        total_raw_words_logged=raw_words_logged,
        effort_points=effort_points,
        daily_target=effective_config.daily_effort_goal,
        goal_met=effort_points >= effective_config.daily_effort_goal,
        premature_revision_blocked=premature_revision_blocked,
        minutes_spent=minutes_spent,
        words_per_hour=wph,
        notes=notes,
    )


class PhaseEffortLedger:
    """Persistent JSONL ledger and portfolio velocity forecaster for Ars Arcanum."""

    def __init__(
        self,
        workspace_root: Path,
        config: EffortMultiplierConfig | None = None,
    ) -> None:
        self.workspace_root = workspace_root.resolve()
        self.config = config or EffortMultiplierConfig()
        self.ledger_path = self.workspace_root / ".arcanum" / "sprint_log.jsonl"

    def append_session(self, session: EvaluatedSession) -> None:
        """Atomically append an `EvaluatedSession` record to `.arcanum/sprint_log.jsonl`."""
        if not is_safe_subpath(self.workspace_root, self.ledger_path):
            raise PathSecurityError(f"Ledger path escapes workspace root: {self.ledger_path}")
        existing = self.ledger_path.read_text(encoding="utf-8") if self.ledger_path.exists() else ""
        line = json.dumps(asdict(session), sort_keys=True) + "\n"
        atomic_write(self.ledger_path, existing + line)

    def log_session(
        self,
        *,
        words_delta: int = 0,
        duration_minutes: float = 0.0,
        stage: str = "Drafting",
        book_title: str = "Manuscript",
        universe: str = "Reliquary",
        series: str = "Standalone",
        notes: str = "",
    ) -> EvaluatedSession:
        """Convenience method to evaluate and append a session record."""
        today = date.today().isoformat()
        session = evaluate_session_effort(
            session_date=today,
            book_title=book_title,
            universe=universe,
            series=series,
            stage=stage,
            first_draft_words=words_delta if words_delta > 0 else 0,
            revision_words=abs(words_delta) if words_delta < 0 else 0,
            minutes_spent=duration_minutes,
            notes=notes,
            config=self.config,
        )
        self.append_session(session)
        return session

    def load_sessions(self) -> list[EvaluatedSession]:
        """Load all logged sessions from `.arcanum/sprint_log.jsonl`."""
        if not self.ledger_path.exists():
            return []
        sessions: list[EvaluatedSession] = []
        for raw_line in self.ledger_path.read_text(encoding="utf-8").splitlines():
            stripped = raw_line.strip()
            if not stripped:
                continue
            data: dict[str, Any] = json.loads(stripped)
            sessions.append(EvaluatedSession(**data))
        return sessions

    def build_dashboard_summary(
        self,
        books: list[BookProjectSpec],
        reference_date: date | None = None,
    ) -> CareerDashboardSummary:
        """Compute career-wide telemetry, universe totals, streak days, and per-book pace forecasts."""
        ref_date = reference_date or date.today()
        ref_iso = ref_date.isoformat()
        sessions = self.load_sessions()

        window_start = ref_date - timedelta(days=29)
        universe_totals: dict[str, int] = {}
        book_manuscript_words: dict[str, int] = {b.book_title: b.initial_words for b in books}
        book_30d_words: dict[str, int] = {b.book_title: 0 for b in books}
        daily_effort_by_date: dict[date, float] = {}
        trailing_30d_total_words = 0
        current_month_words = 0

        for b in books:
            universe_totals.setdefault(b.universe, 0)
            universe_totals[b.universe] += b.initial_words

        for sess in sessions:
            sess_date = date.fromisoformat(sess.session_date)
            added = sess.total_manuscript_words_added
            book_manuscript_words[sess.book_title] = book_manuscript_words.get(sess.book_title, 0) + added
            universe_totals[sess.universe] = universe_totals.get(sess.universe, 0) + added
            daily_effort_by_date[sess_date] = daily_effort_by_date.get(sess_date, 0.0) + sess.effort_points

            if window_start <= sess_date <= ref_date:
                trailing_30d_total_words += added
                book_30d_words[sess.book_title] = book_30d_words.get(sess.book_title, 0) + added

            if sess_date.year == ref_date.year and sess_date.month == ref_date.month:
                current_month_words += added

        lifetime_words = sum(universe_totals.values())
        lifetime_pct = round((lifetime_words / self.config.lifetime_word_milestone) * 100.0, 4)
        trailing_velocity = round(trailing_30d_total_words / 30.0, 1)

        streak = 0
        cursor = ref_date
        while daily_effort_by_date.get(cursor, 0.0) >= self.config.daily_effort_goal:
            streak += 1
            cursor -= timedelta(days=1)

        spotlight: list[BookPipelineTelemetry] = []
        for b in books:
            actual = book_manuscript_words.get(b.book_title, b.initial_words)
            remaining = max(0, b.target_words - actual)
            progress_pct = round((actual / b.target_words) * 100.0, 2) if b.target_words > 0 else 0.0

            deadline_dt = date.fromisoformat(b.deadline)
            start_dt = date.fromisoformat(b.start_date)
            anchor_dt = max(ref_date, start_dt)
            days_left = max(1, (deadline_dt - anchor_dt).days)
            required_pace = round(remaining / days_left) if remaining > 0 else 0

            book_vel_30d = round(book_30d_words.get(b.book_title, 0) / 30.0, 1)
            if remaining == 0:
                forecast_iso = ref_iso
                status = "Completed"
            elif book_vel_30d > 0:
                days_needed = round(remaining / book_vel_30d)
                forecast_iso = (ref_date + timedelta(days=days_needed)).isoformat()
                status = "In Progress"
            else:
                forecast_iso = b.deadline
                status = "Not Started" if actual == 0 else "Paused"

            spotlight.append(
                BookPipelineTelemetry(
                    book_title=b.book_title,
                    universe=b.universe,
                    series=b.series,
                    stage=b.stage.value,
                    target_words=b.target_words,
                    actual_words=actual,
                    progress_pct=progress_pct,
                    days_left=days_left,
                    required_daily_pace=required_pace,
                    trailing_30d_velocity=book_vel_30d,
                    forecasted_finish_date=forecast_iso,
                    status_label=status,
                )
            )

        today_pts = round(daily_effort_by_date.get(ref_date, 0.0), 2)
        monthly_target = round(self.config.annual_word_target / 12)

        return CareerDashboardSummary(
            reference_date=ref_iso,
            lifetime_career_words=lifetime_words,
            lifetime_milestone_pct=lifetime_pct,
            universe_word_totals=universe_totals,
            trailing_30d_velocity_wpd=trailing_velocity,
            active_streak_days=streak,
            current_month_words=current_month_words,
            monthly_word_target=monthly_target,
            today_effort_points=today_pts,
            daily_effort_target=self.config.daily_effort_goal,
            daily_goal_met=today_pts >= self.config.daily_effort_goal,
            book_spotlight=tuple(spotlight),
        )


# ==============================================================================
# Sprint Lifecycle & Hybrid Velocity Analytics
# ==============================================================================

def _get_arcanum_dir(ms_dir: Path) -> Path:
    """Returns the .arcanum hidden metadata directory for a manuscript or project."""
    arc_dir = ms_dir / ".arcanum"
    arc_dir.mkdir(parents=True, exist_ok=True)
    return arc_dir


def _get_state_file(ms_dir: Path) -> Path:
    """Returns the path to the active sprint state lock file."""
    return _get_arcanum_dir(ms_dir) / ".sprint_state.json"


def _get_log_file(ms_dir: Path) -> Path:
    """Returns the path to the historical sprint JSONL log file."""
    return _get_arcanum_dir(ms_dir) / "sprint_log.jsonl"


def _count_current_manuscript_words(ms_dir: Path, chapter_file: str | None = None) -> int:
    """Computes current total words in the manuscript or target chapter."""
    if chapter_file:
        target_path = Path(chapter_file)
        if not target_path.is_file():
            target_path = ms_dir / chapter_file
        if target_path.is_file():
            try:
                content = target_path.read_text(encoding="utf-8", errors="replace")
                return int(count_prose_words(content))
            except Exception:
                return 0

    total = 0
    for md_file in ms_dir.rglob("*.md"):
        if (
            not md_file.name.startswith((".", "_"))
            and "Backups" not in md_file.parts
            and ".arcanum" not in md_file.parts
        ):
            try:
                txt = md_file.read_text(encoding="utf-8", errors="replace")
                total += count_prose_words(txt)
            except Exception:
                pass
    return total


def _resolve_target_dir(target_dir: Path | str) -> Path:
    """Resolves manuscript path using scope helper if available, falling back to Path."""
    try:
        from src.arcanum.core.scope import resolve_manuscript_path
        p = resolve_manuscript_path(target_dir)
        if p:
            return Path(p).resolve()
    except ImportError:
        try:
            from scripts.lib.scope import resolve_manuscript_path
            p = resolve_manuscript_path(target_dir)
            if p:
                return Path(p).resolve()
        except ImportError:
            pass
    return Path(target_dir).resolve()


def start_sprint(
    target_dir: Path | str,
    target_words: int = 500,
    minutes: int = 25,
    chapter: str | None = None,
    interactive: bool = False,
    force: bool = False,
) -> dict[str, Any]:
    """Starts a new sprint session and writes state to .arcanum/.sprint_state.json."""
    ms_path = _resolve_target_dir(target_dir)
    if not ms_path.is_dir():
        raise FileNotFoundError(f"Manuscript directory not found: {target_dir}")

    state_file = _get_state_file(ms_path)
    if state_file.is_file() and not force:
        try:
            existing = json.loads(state_file.read_text(encoding="utf-8", errors="replace"))
            raise RuntimeError(
                f"An active sprint is already running (started at {existing.get('timestamp')}). "
                "Run 'arcanum sprint stop' to conclude it or 'arcanum sprint cancel' to abort."
            )
        except json.JSONDecodeError:
            pass

    initial_words = _count_current_manuscript_words(ms_path, chapter)
    session_id = f"sprint_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    timestamp_iso = datetime.datetime.now().isoformat()
    start_unix = time.time()

    state = {
        "session_id": session_id,
        "timestamp": timestamp_iso,
        "start_time_unix": start_unix,
        "target_words": int(target_words),
        "planned_duration_min": int(minutes),
        "manuscript_dir": str(ms_path),
        "chapter_target": chapter or "",
        "initial_word_count": initial_words,
    }

    atomic_write(state_file, json.dumps(state, indent=2))

    if interactive and hasattr(sys.stdout, "isatty") and sys.stdout.isatty():
        _run_interactive_tty_timer(ms_path, state)

    return {
        "status": "started",
        "session_id": session_id,
        "timestamp": timestamp_iso,
        "target_words": target_words,
        "duration_minutes": minutes,
        "initial_word_count": initial_words,
        "chapter": chapter or "Full Manuscript",
    }


def _run_interactive_tty_timer(ms_path: Path, state: dict[str, Any]) -> None:
    """Runs a live countdown timer in interactive TTY mode."""
    duration_sec = state["planned_duration_min"] * 60
    start_time = state["start_time_unix"]
    target_words = state["target_words"]
    ch = state.get("chapter_target") or "Manuscript"

    print(f"\n🚀 Writing Sprint Started! Target: {target_words:,} words in {state['planned_duration_min']} min ({ch})")
    print("Press Ctrl+C at any time to finish or pause.\n")

    try:
        while True:
            elapsed = time.time() - start_time
            remaining = max(0, duration_sec - elapsed)
            rem_m = int(remaining // 60)
            rem_s = int(remaining % 60)
            pct = min(100.0, (elapsed / max(1, duration_sec)) * 100.0)

            sys.stdout.write(f"\r⏱️  Time Remaining: \033[1;36m{rem_m:02d}:{rem_s:02d}\033[0m ({pct:4.1f}%) | Goal: {target_words}w   ")
            sys.stdout.flush()

            if remaining <= 0:
                print("\n\n🎉 Sprint Duration Complete! Time is up!")
                break
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\n\n⏸️ Sprint timer stopped by user.")


def status_sprint(target_dir: Path | str) -> dict[str, Any]:
    """Queries the currently active sprint session."""
    ms_path = _resolve_target_dir(target_dir)
    state_file = _get_state_file(ms_path)
    if not state_file.is_file():
        return {"status": "inactive", "message": "No active sprint session running."}

    try:
        state = json.loads(state_file.read_text(encoding="utf-8", errors="replace"))
    except Exception as e:
        return {"status": "error", "message": f"Corrupted sprint state file: {e}"}

    start_unix = state.get("start_time_unix", time.time())
    elapsed_min = round((time.time() - start_unix) / 60.0, 1)
    planned_min = state.get("planned_duration_min", 25)
    target_words = state.get("target_words", 500)
    init_words = state.get("initial_word_count", 0)
    ch = state.get("chapter_target") or None

    cur_words = _count_current_manuscript_words(ms_path, ch)
    delta_words = max(0, cur_words - init_words)
    wpm = round(delta_words / max(0.1, elapsed_min), 1)

    return {
        "status": "active",
        "session_id": state.get("session_id"),
        "started_at": state.get("timestamp"),
        "elapsed_minutes": elapsed_min,
        "planned_duration_min": planned_min,
        "target_words": target_words,
        "initial_words": init_words,
        "current_words": cur_words,
        "words_written": delta_words,
        "instantaneous_wpm": wpm,
        "chapter": ch or "Full Manuscript",
    }


def stop_sprint(
    target_dir: Path | str,
    manual_words: int | None = None,
) -> dict[str, Any]:
    """Concludes the active sprint session, logs record to sprint_log.jsonl, and removes state lock."""
    ms_path = _resolve_target_dir(target_dir)
    state_file = _get_state_file(ms_path)
    if not state_file.is_file():
        raise RuntimeError("No active sprint session found. Use 'arcanum sprint start' first.")

    try:
        state = json.loads(state_file.read_text(encoding="utf-8", errors="replace"))
    except Exception as e:
        state_file.unlink(missing_ok=True)
        raise RuntimeError(f"Corrupted sprint state file cleared: {e}") from e

    start_unix = state.get("start_time_unix", time.time())
    duration_min = round(max(0.1, (time.time() - start_unix) / 60.0), 2)
    target_words = state.get("target_words", 500)
    init_words = state.get("initial_word_count", 0)
    ch = state.get("chapter_target") or ""

    if manual_words is not None:
        words_written = int(manual_words)
    else:
        cur_words = _count_current_manuscript_words(ms_path, ch if ch else None)
        words_written = max(0, cur_words - init_words)

    wpm = round(words_written / duration_min, 2)
    wph = round(wpm * 60, 1)
    ratio = round(words_written / max(1, target_words), 3)

    record = {
        "session_id": state.get("session_id"),
        "timestamp": datetime.datetime.now().isoformat(),
        "duration_min": duration_min,
        "words_written": words_written,
        "wpm": wpm,
        "wph": wph,
        "target": target_words,
        "completion_ratio": ratio,
        "chapter": ch,
    }

    # Append to JSONL log atomically
    log_file = _get_log_file(ms_path)
    record_line = json.dumps(record) + "\n"
    existing = log_file.read_text(encoding="utf-8") if log_file.exists() else ""
    atomic_write(log_file, existing + record_line)

    # Clean up state lock file
    state_file.unlink(missing_ok=True)

    return {
        "status": "completed",
        "session_id": record["session_id"],
        "duration_minutes": duration_min,
        "words_written": words_written,
        "target_words": target_words,
        "wpm": wpm,
        "wph": wph,
        "completion_ratio": ratio,
        "completion_percentage": round(ratio * 100.0, 1),
        "chapter": ch or "Full Manuscript",
    }


def cancel_sprint(target_dir: Path | str) -> dict[str, Any]:
    """Aborts the active sprint session without saving to sprint_log.jsonl."""
    ms_path = _resolve_target_dir(target_dir)
    state_file = _get_state_file(ms_path)
    if state_file.is_file():
        state_file.unlink(missing_ok=True)
        return {"status": "cancelled", "message": "Active sprint session cancelled."}
    return {"status": "inactive", "message": "No active sprint session was running."}


def log_manual_sprint(
    target_dir: Path | str,
    words: int,
    minutes: float = 25.0,
    timestamp: str | None = None,
    target_words: int = 500,
    chapter: str = "",
) -> dict[str, Any]:
    """Manually records a completed writing session into .arcanum/sprint_log.jsonl."""
    ms_path = _resolve_target_dir(target_dir)
    if not ms_path.is_dir():
        raise FileNotFoundError(f"Manuscript directory not found: {target_dir}")

    ts = timestamp or datetime.datetime.now().isoformat()
    duration = max(0.1, float(minutes))
    wpm = round(words / duration, 2)
    wph = round(wpm * 60, 1)
    ratio = round(words / max(1, target_words), 3)
    session_id = f"manual_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

    record = {
        "session_id": session_id,
        "timestamp": ts,
        "duration_min": duration,
        "words_written": int(words),
        "wpm": wpm,
        "wph": wph,
        "target": int(target_words),
        "completion_ratio": ratio,
        "chapter": chapter,
    }

    log_file = _get_log_file(ms_path)
    record_line = json.dumps(record) + "\n"
    existing = log_file.read_text(encoding="utf-8") if log_file.exists() else ""
    atomic_write(log_file, existing + record_line)

    return {
        "status": "logged",
        "record": record,
    }


def get_velocity_metrics(target_dir: Path | str) -> dict[str, Any]:
    """Hybrid velocity engine aggregating drafting logs across:

    1. .arcanum/sprint_log.jsonl
    2. Obsidian Daily-Writing-Log markdown files
    3. Historical snapshot / git commit timestamp deltas
    """
    ms_path = _resolve_target_dir(target_dir)
    sprints: list[dict[str, Any]] = []

    # Source 1: .arcanum/sprint_log.jsonl
    log_file = _get_log_file(ms_path)
    if log_file.is_file():
        for line in log_file.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line:
                try:
                    sprints.append(json.loads(line))
                except Exception:
                    pass

    # Source 2: Scan for Obsidian Daily-Writing-Log markdown notes
    seen_files: set[Path] = set()
    search_dirs = [ms_path]
    if ms_path.parent.is_dir() and ms_path.parent != ms_path:
        search_dirs.append(ms_path.parent)

    extract_fm = None
    try:
        from src.arcanum.core.frontmatter import extract_frontmatter_and_body as _efm
        extract_fm = _efm
    except ImportError:
        try:
            from scripts.lib.frontmatter import extract_frontmatter_and_body as _efm
            extract_fm = _efm
        except ImportError:
            pass

    for s_dir in search_dirs:
        for f in s_dir.rglob("*.md"):
            real_f = f.resolve()
            if real_f in seen_files:
                continue
            seen_files.add(real_f)

            if real_f.is_file() and ("Writing-Log" in real_f.name or "WritingLog" in real_f.name):
                if "Templates" in real_f.parts or "templates" in real_f.parts:
                    continue
                try:
                    content = real_f.read_text(encoding="utf-8", errors="replace")
                    fm: dict[str, Any] = {}
                    if extract_fm:
                        fm, _ = extract_fm(content)
                    else:
                        m = _FRONTMATTER_PATTERN.match(content)
                        if m:
                            for ln in m.group(1).splitlines():
                                if ":" in ln:
                                    k, v = ln.split(":", 1)
                                    fm[k.strip()] = v.strip().strip("'\"")

                    if fm.get("fileClass") == "WritingLog" or fm.get("type") == "daily_writing_log":
                        date_raw = str(fm.get("date", ""))
                        if date_raw.startswith("<%") or not date_raw:
                            continue
                        words_w = int(fm.get("words_written", 0))
                        time_m = float(fm.get("writing_time_minutes", 25.0))
                        wpm_val = float(fm.get("wpm_velocity", words_w / max(0.1, time_m)))
                        goal = int(fm.get("goal") or fm.get("dailyGoal") or fm.get("target_words_daily") or 1000)

                        sprints.append({
                            "session_id": f"obsidian_{real_f.stem}",
                            "timestamp": f"{date_raw}T12:00:00",
                            "duration_min": time_m,
                            "words_written": words_w,
                            "wpm": round(wpm_val, 2),
                            "wph": round(wpm_val * 60, 1),
                            "target": goal,
                            "completion_ratio": round(words_w / max(1, goal), 3),
                            "chapter": str(fm.get("scene_worked_on", "")),
                        })
                except Exception:
                    pass

    # Sort sprints chronologically
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
    active_days: set[str] = set()
    tod_dist = {"Morning (6-12)": 0, "Afternoon (12-18)": 0, "Evening (18-24)": 0, "Night (0-6)": 0}

    for s in sprints:
        ts_str = str(s.get("timestamp", ""))
        try:
            ts_dt = datetime.datetime.fromisoformat(ts_str[:19])
        except (ValueError, TypeError):
            continue

        day_key = ts_dt.strftime("%Y-%m-%d")
        active_days.add(day_key)
        w = s.get("words_written", 0)
        m = s.get("duration_min", 0.0)

        hr = ts_dt.hour
        if 6 <= hr < 12:
            tod_dist["Morning (6-12)"] += w
        elif 12 <= hr < 18:
            tod_dist["Afternoon (12-18)"] += w
        elif 18 <= hr < 24:
            tod_dist["Evening (18-24)"] += w
        else:
            tod_dist["Night (0-6)"] += w

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

    cur_streak = 0
    best_streak = 0
    sorted_days = sorted([datetime.date.fromisoformat(d) for d in active_days])

    if sorted_days:
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)

        check_day = today if today in sorted_days else (yesterday if yesterday in sorted_days else None)
        if check_day:
            temp_streak = 0
            curr_check = check_day
            day_set = set(sorted_days)
            while curr_check in day_set:
                temp_streak += 1
                curr_check -= datetime.timedelta(days=1)
            cur_streak = temp_streak

        temp_best = 1
        curr_run = 1
        for i in range(1, len(sorted_days)):
            if (sorted_days[i] - sorted_days[i - 1]).days == 1:
                curr_run += 1
                if curr_run > temp_best:
                    temp_best = curr_run
            else:
                curr_run = 1
        best_streak = temp_best if sorted_days else 0

    return {
        "total_sprint_sessions": total_sessions,
        "total_sprint_words": total_words,
        "total_sprint_minutes": round(total_minutes, 1),
        "overall_average_wpm": overall_wpm,
        "rolling_7d_daily_words": rolling_7d_wpd,
        "rolling_7d_wpm": rolling_7d_wpm,
        "rolling_30d_daily_words": rolling_30d_wpd,
        "rolling_30d_wpm": rolling_30d_wpm,
        "current_streak_days": cur_streak,
        "best_streak_days": best_streak,
        "time_of_day_distribution": tod_dist,
        "sprint_history": sprints,
    }


def format_stats_table(vel: dict[str, Any], title: str = "Manuscript") -> str:
    """Formats velocity statistics into an ANSI terminal report."""
    lines: list[str] = []
    lines.append(f"⚡  {title} — Drafting Velocity & Sprint Telemetry")
    lines.append("═" * 70)
    lines.append(f"  Total Sprints:    {vel.get('total_sprint_sessions', 0):>6} sessions")
    lines.append(f"  Sprint Words:     {vel.get('total_sprint_words', 0):>6,} words ({vel.get('total_sprint_minutes', 0):.0f} active minutes)")
    lines.append(f"  All-Time Velocity: {vel.get('overall_average_wpm', 0):>5.1f} WPM ({vel.get('overall_average_wpm', 0)*60:>6.0f} WPH)")
    lines.append("─" * 70)
    lines.append(f"  7-Day Rolling:    {vel.get('rolling_7d_daily_words', 0):>6,} words/day ({vel.get('rolling_7d_wpm', 0):.1f} WPM)")
    lines.append(f"  30-Day Rolling:   {vel.get('rolling_30d_daily_words', 0):>6,} words/day ({vel.get('rolling_30d_wpm', 0):.1f} WPM)")
    lines.append(f"  Daily Streak:     {vel.get('current_streak_days', 0):>6} days (Best: {vel.get('best_streak_days', 0)} days)")
    lines.append("═" * 70)

    tod = vel.get("time_of_day_distribution", {})
    if any(tod.values()):
        lines.append("\n🌅  Drafting Velocity by Time of Day:")
        tot_tod = max(1, sum(tod.values()))
        for k, v in tod.items():
            pct = (v / tot_tod) * 100.0
            lines.append(f"  • {k:<20} {v:>7,} words ({pct:5.1f}%)")

    history = vel.get("sprint_history", [])
    if history:
        lines.append("\n📋  Recent Sprints (Last 5):")
        lines.append(f"{'Date/Time':<18} {'Target':<14} {'Min':>6} {'Words':>8} {'WPM':>8} {'Ratio':>8}")
        lines.append("─" * 70)
        for s in reversed(history[-5:]):
            ts = str(s.get("timestamp", ""))[:16].replace("T", " ")
            ch = str(s.get("chapter", ""))[:12] or "General"
            dur = s.get("duration_min", 0.0)
            w = s.get("words_written", 0)
            wpm = s.get("wpm", 0.0)
            rat = s.get("completion_ratio", 0.0) * 100.0
            lines.append(f"{ts:<18} {ch:<14} {dur:>6.1f} {w:>8,} {wpm:>8.1f} {rat:>7.0f}%")

    return "\n".join(lines)


def format_stats_markdown(vel: dict[str, Any], title: str = "Manuscript") -> str:
    """Formats velocity statistics as GitHub Markdown."""
    lines: list[str] = []
    lines.append(f"# {title} — Drafting Velocity & Sprint Telemetry\n")
    lines.append(f"- **Total Sprint Sessions**: {vel.get('total_sprint_sessions', 0)}")
    lines.append(f"- **Sprint Words Written**: {vel.get('total_sprint_words', 0):,} words")
    lines.append(f"- **All-Time Average Velocity**: {vel.get('overall_average_wpm', 0):.1f} WPM")
    lines.append(f"- **7-Day Rolling Pace**: {vel.get('rolling_7d_daily_words', 0):,} words/day")
    lines.append(f"- **Active Habit Streak**: {vel.get('current_streak_days', 0)} consecutive days (Best: {vel.get('best_streak_days', 0)} days)\n")

    history = vel.get("sprint_history", [])
    if history:
        lines.append("## Recent Sprint Sessions\n")
        lines.append("| Date/Time | Target Chapter | Duration (min) | Words | WPM | Target Completion |")
        lines.append("| :--- | :--- | ---: | ---: | ---: | ---: |")
        for s in reversed(history[-10:]):
            ts = str(s.get("timestamp", ""))[:16].replace("T", " ")
            ch = str(s.get("chapter", "")) or "General"
            lines.append(f"| {ts} | {ch} | {s.get('duration_min', 0):.1f} | {s.get('words_written', 0):,} | {s.get('wpm', 0):.1f} | {s.get('completion_ratio', 0)*100:.0f}% |")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for `arcanum sprint` and `arcanum sprint-effort`."""
    if argv and argv[0] == "effort":
        effort_parser = argparse.ArgumentParser(
            prog="arcanum sprint effort",
            description="Log a phase-weighted writing session and evaluate daily effort points.",
        )
        effort_parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Path to sovereign workspace root")
        effort_parser.add_argument("--book", required=True, help="Book title (e.g., 'Prisoner of Sand Sea')")
        effort_parser.add_argument("--universe", default="Reliquary", help="Universe name (default: Reliquary)")
        effort_parser.add_argument("--series", default="Sand Sea Saga", help="Series name")
        effort_parser.add_argument(
            "--stage",
            default=ProjectStage.DRAFTING.value,
            choices=[s.value for s in ProjectStage],
            help="Current project lifecycle stage",
        )
        effort_parser.add_argument("--date", default=date.today().isoformat(), help="Session ISO date (YYYY-MM-DD)")
        effort_parser.add_argument("--worldbuilding", type=int, default=0, help="Worldbuilding / lore words written")
        effort_parser.add_argument("--outlining", type=int, default=0, help="Outlining words written")
        effort_parser.add_argument("--draft", type=int, default=0, help="First-draft prose words written")
        effort_parser.add_argument("--revision", type=int, default=0, help="Revision words edited")
        effort_parser.add_argument("--minutes", type=float, default=0.0, help="Session duration in minutes")
        effort_parser.add_argument("--notes", default="", help="Optional session notes or scene breakdown")
        eff_args = effort_parser.parse_args(argv[1:])

        session = evaluate_session_effort(
            session_date=eff_args.date,
            book_title=eff_args.book,
            universe=eff_args.universe,
            series=eff_args.series,
            stage=ProjectStage(eff_args.stage),
            worldbuilding_words=eff_args.worldbuilding,
            outlining_words=eff_args.outlining,
            first_draft_words=eff_args.draft,
            revision_words=eff_args.revision,
            minutes_spent=eff_args.minutes,
            notes=eff_args.notes,
        )
        ledger = PhaseEffortLedger(eff_args.workspace)
        ledger.append_session(session)
        sys.stdout.write(json.dumps(asdict(session), indent=2) + "\n")
        return 0

    parser = argparse.ArgumentParser(description="Ars Arcanum Writing Sprint & Cognitive Velocity Engine")
    subparsers = parser.add_subparsers(dest="command", help="Sprint sub-command")

    # effort
    subparsers.add_parser("effort", help="Log a phase-weighted writing session and evaluate daily effort points")

    # start
    p_start = subparsers.add_parser("start", help="Start a new writing sprint session")
    p_start.add_argument("manuscript", nargs="?", default=".", help="Manuscript directory")
    p_start.add_argument("--target", "-t", type=int, default=500, help="Target word count (default: 500)")
    p_start.add_argument("--minutes", "-m", type=int, default=25, help="Sprint duration in minutes (default: 25)")
    p_start.add_argument("--chapter", "-c", help="Specific chapter filename target")
    p_start.add_argument("--no-interactive", "-n", action="store_true", help="Start in non-interactive background mode")
    p_start.add_argument("--force", "-f", action="store_true", help="Force start and overwrite stale sprint state")
    p_start.add_argument("--json", action="store_true", help="Output JSON results")

    # stop
    p_stop = subparsers.add_parser("stop", help="Stop the active sprint session and record words")
    p_stop.add_argument("manuscript", nargs="?", default=".", help="Manuscript directory")
    p_stop.add_argument("--words", "-w", type=int, help="Manual words written override (default: auto-computed)")
    p_stop.add_argument("--json", action="store_true", help="Output JSON results")

    # status
    p_stat = subparsers.add_parser("status", help="Query active sprint session status")
    p_stat.add_argument("manuscript", nargs="?", default=".", help="Manuscript directory")
    p_stat.add_argument("--json", action="store_true", help="Output JSON results")

    # cancel / abort
    p_cancel = subparsers.add_parser("cancel", help="Cancel and abort active sprint session without saving")
    p_cancel.add_argument("manuscript", nargs="?", default=".", help="Manuscript directory")
    p_cancel.add_argument("--json", action="store_true", help="Output JSON results")

    # log
    p_log = subparsers.add_parser("log", help="Manually log a completed sprint session")
    p_log.add_argument("manuscript", nargs="?", default=".", help="Manuscript directory")
    p_log.add_argument("--words", "-w", type=int, required=True, help="Words written")
    p_log.add_argument("--minutes", "-m", type=float, default=25.0, help="Duration in minutes (default: 25)")
    p_log.add_argument("--target", "-t", type=int, default=500, help="Target word goal")
    p_log.add_argument("--chapter", "-c", default="", help="Chapter name")
    p_log.add_argument("--json", action="store_true", help="Output JSON results")

    # stats / history
    p_hist = subparsers.add_parser("stats", help="Display drafting velocity and sprint history statistics")
    p_hist.add_argument("manuscript", nargs="?", default=".", help="Manuscript directory")
    p_hist.add_argument("--json", action="store_true", help="Output JSON results")
    p_hist.add_argument("--md", action="store_true", help="Output Markdown report")
    p_hist.add_argument("--html", help="Generate standalone offline HTML5 Velocity Studio")
    p_hist.add_argument("--open", action="store_true", help="Open generated HTML5 Velocity Studio in default browser")

    # report
    p_rep = subparsers.add_parser("report", help="Generate standalone HTML5 Velocity & Sprint Studio")
    p_rep.add_argument("manuscript", nargs="?", default=".", help="Manuscript directory")
    p_rep.add_argument("--html", "-o", default="dist/velocity_studio.html", help="Output HTML file path")
    p_rep.add_argument("--open", action="store_true", help="Open generated HTML5 Velocity Studio in default browser")
    p_rep.add_argument("--json", action="store_true", help="Output JSON results")

    args = parser.parse_args(argv)
    cmd = args.command or "status"
    ms_dir = getattr(args, "manuscript", ".")

    try:
        if cmd == "start":
            res = start_sprint(
                ms_dir,
                target_words=args.target,
                minutes=args.minutes,
                chapter=args.chapter,
                interactive=not args.no_interactive,
                force=args.force,
            )
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                print(f"🚀 Sprint session started: {res['session_id']} (Goal: {res['target_words']}w in {res['duration_minutes']}m)")
            return 0

        if cmd == "stop":
            res = stop_sprint(ms_dir, manual_words=args.words)
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                print(f"🎉 Sprint Finished! Words: {res['words_written']:,} in {res['duration_minutes']}m ({res['wpm']:.1f} WPM, {res['completion_percentage']}% of goal)")
            return 0

        if cmd == "status":
            res = status_sprint(ms_dir)
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                if res["status"] == "active":
                    print(f"⏱️  Active Sprint: {res['session_id']} | Elapsed: {res['elapsed_minutes']}m / {res['planned_duration_min']}m | Written: {res['words_written']}w ({res['instantaneous_wpm']} WPM)")
                else:
                    print("No active sprint session running. Run 'arcanum sprint start' to begin.")
            return 0

        if cmd == "cancel":
            res = cancel_sprint(ms_dir)
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                print(res["message"])
            return 0

        if cmd == "log":
            res = log_manual_sprint(
                ms_dir,
                words=args.words,
                minutes=args.minutes,
                target_words=args.target,
                chapter=args.chapter,
            )
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                print(f"✓ Sprint logged: {args.words:,} words in {args.minutes} min ({res['record']['wpm']} WPM)")
            return 0

        if cmd in ("stats", "report"):
            vel = get_velocity_metrics(ms_dir)
            html_out = getattr(args, "html", None)
            open_browser = getattr(args, "open", False)
            if not html_out and open_browser:
                html_out = "dist/velocity_studio.html"

            render_vel = None
            try:
                from scripts.lib.velocity_template import render_velocity_html as _rvh
                render_vel = _rvh
            except ImportError:
                try:
                    from lib.velocity_template import render_velocity_html as _rvh
                    render_vel = _rvh
                except ImportError:
                    pass

            if html_out and render_vel:
                w_data = {"title": "Manuscript", "total_words": vel.get("total_sprint_words", 0)}
                try:
                    from src.arcanum.manuscript.word_counter import analyze_manuscript_words
                    w_data = analyze_manuscript_words(ms_dir)
                except Exception:
                    try:
                        from scripts.lib.word_counter import analyze_manuscript_words
                        w_data = analyze_manuscript_words(ms_dir)
                    except Exception:
                        pass
                render_vel(w_data, vel, html_out)
                print(f"✓ Standalone Velocity Studio written to: {html_out}")
                if open_browser:
                    import webbrowser
                    try:
                        webbrowser.open(Path(html_out).resolve().as_uri())
                    except Exception as exc:
                        print(f"Warning: Could not open browser: {exc}", file=sys.stderr)
                return 0

            if getattr(args, "json", False):
                print(json.dumps(vel, indent=2))
            elif getattr(args, "md", False):
                print(format_stats_markdown(vel))
            else:
                print(format_stats_table(vel))
            return 0

        parser.print_help()
        return 0

    except Exception as e:
        if getattr(args, "json", False):
            print(json.dumps({"status": "error", "error": str(e)}, indent=2))
        else:
            print(f"Error: {e}", file=sys.stderr)
        return 1


__all__ = [
    "BookPipelineTelemetry",
    "BookProjectSpec",
    "CareerDashboardSummary",
    "DESIGNATED_OUTLINE_STAGES",
    "DESIGNATED_REVISION_STAGES",
    "EffortMultiplierConfig",
    "EvaluatedSession",
    "PhaseEffortLedger",
    "ProjectStage",
    "SessionEffortBreakdown",
    "cancel_sprint",
    "count_prose_words",
    "evaluate_session_effort",
    "format_stats_markdown",
    "format_stats_table",
    "get_velocity_metrics",
    "log_manual_sprint",
    "main",
    "start_sprint",
    "status_sprint",
    "stop_sprint",
]
