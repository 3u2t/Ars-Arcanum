"""Phase-Aware Effort & Career Velocity Engine for Ars Arcanum (`writing_sprint.py` & `portfolio.py`).

Natively unifies the authorial career pipeline and phase-weighted productivity rules into
Ars Arcanum's local-first CLI & JSONL telemetry:
- 9 Canonical Project Stages: `Concept`, `Pre-Draft Outline`, `Drafting`, `Pre-Revision Outline`,
  `Revision`, `Beta Review`, `Proofing`, `Querying`, `Publishing`.
- Deterministic Phase-Aware Effort Multipliers:
  * First Draft Prose (`first_draft_words`): `1.00x` across all stages.
  * Outlining (`outlining_words`): `1.00x` during designated Outline stages, `0.50x` off-phase.
  * Worldbuilding / Lore (`worldbuilding_words`): `0.50x` (2 lore words = 1 effort point).
  * Revisions (`revision_words`): `0.20x` during Revision/Beta/Proofing stages, and `0.00x`
    outside Revision stages to prevent premature editing during First Draft sprints.

Repository Target: `scripts/lib/phase_effort_engine.py`
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from enum import Enum
import json
from pathlib import Path
import sys
from typing import Any

try:
    from lib.vault_index import atomic_write, is_safe_subpath
except ImportError:
    from vault_index import atomic_write, is_safe_subpath


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


DESIGNATED_OUTLINE_STAGES: frozenset[ProjectStage] = frozenset(
    {
        ProjectStage.CONCEPT,
        ProjectStage.PRE_DRAFT_OUTLINE,
        ProjectStage.PRE_REVISION_OUTLINE,
    }
)

DESIGNATED_REVISION_STAGES: frozenset[ProjectStage] = frozenset(
    {
        ProjectStage.REVISION,
        ProjectStage.BETA_REVIEW,
        ProjectStage.PROOFING,
    }
)


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
    config: EffortMultiplierConfig = EffortMultiplierConfig(),
) -> EvaluatedSession:
    """Deterministically compute effort points and manuscript progress for a writing session."""
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
        config.on_phase_outlining_weight
        if resolved_stage in DESIGNATED_OUTLINE_STAGES
        else config.off_phase_outlining_weight
    )
    in_revision_stage = resolved_stage in DESIGNATED_REVISION_STAGES
    revision_mult = config.on_phase_revision_weight if in_revision_stage else config.off_phase_revision_weight

    effort_points = round(
        (first_draft_words * config.drafting_weight)
        + (outlining_words * outline_mult)
        + (worldbuilding_words * config.worldbuilding_weight)
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
        daily_target=config.daily_effort_goal,
        goal_met=effort_points >= config.daily_effort_goal,
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
        config: EffortMultiplierConfig = EffortMultiplierConfig(),
    ) -> None:
        self.workspace_root = workspace_root.resolve()
        self.config = config
        self.ledger_path = self.workspace_root / ".arcanum" / "sprint_log.jsonl"

    def append_session(self, session: EvaluatedSession) -> None:
        """Atomically append an `EvaluatedSession` record to `.arcanum/sprint_log.jsonl`."""
        if not is_safe_subpath(self.workspace_root, self.ledger_path):
            raise PermissionError(f"Ledger path escapes workspace root: {self.ledger_path}")
        existing = self.ledger_path.read_text(encoding="utf-8") if self.ledger_path.exists() else ""
        line = json.dumps(asdict(session), sort_keys=True) + "\n"
        atomic_write(self.ledger_path, existing + line)

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


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for `arcanum sprint-effort` / `arcanum effort`."""
    parser = argparse.ArgumentParser(
        prog="arcanum sprint-effort",
        description="Log a phase-weighted writing session and evaluate daily effort points.",
    )
    parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Path to sovereign workspace root")
    parser.add_argument("--book", required=True, help="Book title (e.g., 'Prisoner of Sand Sea')")
    parser.add_argument("--universe", default="Reliquary", help="Universe name (default: Reliquary)")
    parser.add_argument("--series", default="Sand Sea Saga", help="Series name")
    parser.add_argument(
        "--stage",
        default=ProjectStage.DRAFTING.value,
        choices=[s.value for s in ProjectStage],
        help="Current project lifecycle stage",
    )
    parser.add_argument("--date", default=date.today().isoformat(), help="Session ISO date (YYYY-MM-DD)")
    parser.add_argument("--worldbuilding", type=int, default=0, help="Worldbuilding / lore words written")
    parser.add_argument("--outlining", type=int, default=0, help="Outlining words written")
    parser.add_argument("--draft", type=int, default=0, help="First-draft prose words written")
    parser.add_argument("--revision", type=int, default=0, help="Revision words edited")
    parser.add_argument("--minutes", type=float, default=0.0, help="Session duration in minutes")
    parser.add_argument("--notes", default="", help="Optional session notes or scene breakdown")
    args = parser.parse_args(argv)

    session = evaluate_session_effort(
        session_date=args.date,
        book_title=args.book,
        universe=args.universe,
        series=args.series,
        stage=ProjectStage(args.stage),
        worldbuilding_words=args.worldbuilding,
        outlining_words=args.outlining,
        first_draft_words=args.draft,
        revision_words=args.revision,
        minutes_spent=args.minutes,
        notes=args.notes,
    )
    ledger = PhaseEffortLedger(args.workspace)
    ledger.append_session(session)
    sys.stdout.write(json.dumps(asdict(session), indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
