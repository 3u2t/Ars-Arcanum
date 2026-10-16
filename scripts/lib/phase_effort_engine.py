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
Delegated natively to: `src.arcanum.manuscript.velocity`
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path if needed
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Module-level aliases for sys.modules compatibility
for _alias in ("phase_effort_engine", "lib.phase_effort_engine", "scripts.lib.phase_effort_engine"):
    sys.modules.setdefault(_alias, sys.modules[__name__])

from src.arcanum.manuscript.velocity import (  # noqa: E402
    DESIGNATED_OUTLINE_STAGES,
    DESIGNATED_REVISION_STAGES,
    BookPipelineTelemetry,
    BookProjectSpec,
    CareerDashboardSummary,
    EffortMultiplierConfig,
    EvaluatedSession,
    PhaseEffortLedger,
    ProjectStage,
    SessionEffortBreakdown,
    evaluate_session_effort,
)
from src.arcanum.manuscript.velocity import main as _native_main  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint forwarding to `arcanum sprint-effort` / `arcanum effort`."""
    args = argv if argv is not None else sys.argv[1:]
    return _native_main(["effort", *args])


__all__ = [
    "DESIGNATED_OUTLINE_STAGES",
    "DESIGNATED_REVISION_STAGES",
    "BookPipelineTelemetry",
    "BookProjectSpec",
    "CareerDashboardSummary",
    "EffortMultiplierConfig",
    "EvaluatedSession",
    "PhaseEffortLedger",
    "ProjectStage",
    "SessionEffortBreakdown",
    "evaluate_session_effort",
    "main",
]

if __name__ == "__main__":
    raise SystemExit(main())
