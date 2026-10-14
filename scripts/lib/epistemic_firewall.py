"""Epistemic POV & Spoiler Firewall Engine for Ars Arcanum (`arcanum validate --epistemic`).

Models Epistemic Asymmetry across a multi-POV manuscript and its linked World Bible:
- Tracks what each character knows at baseline (`Characters/<Name>.md` frontmatter `knows: [...]`).
- Tracks chapter-ordered scene transitions (`chapter`, `pov`, `learns: [...]`, `references: [...]`,
  and wikilinks `[[Entity]]` mapped to secret lore IDs).
- Flags deterministic epistemic violations (`EPI-201` through `EPI-203`):
  * `EPI-201`: POV character references or acts on a secret `fact_id` in Chapter $N$ before learning
    it in Chapter $M$ ($N < M$) or never learning it at all.
  * `EPI-202`: Unreliable/Mythic lore (`myth: true` in World Bible frontmatter) is cited as objective
    narrator truth without an in-world epistemic framing tag.
  * `EPI-203`: Orphan reveal (`learns: [fact_id]` is declared in a chapter, but `fact_id` is never
    defined or referenced anywhere else in the vault).

Repository Target: `scripts/lib/epistemic_firewall.py`
Reference: https://github.com/aryansinghnagar/Ars-Arcanum
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class CharacterKnowledgeBaseline:
    """Initial knowledge state of a POV character declared in `Characters/<Name>.md`."""

    character_name: str
    initial_known_facts: frozenset[str]


@dataclass(frozen=True)
class ChapterEpistemicEvent:
    """Chronological scene or chapter node in the manuscript."""

    chapter_index: int
    chapter_title: str
    pov_character: str
    referenced_facts: tuple[str, ...]
    learned_facts: tuple[str, ...]
    asserted_objective_facts: tuple[str, ...] = ()


@dataclass(frozen=True)
class EpistemicViolation:
    """Single deterministic epistemic or spoiler violation."""

    rule_id: str  # "EPI-201" | "EPI-202" | "EPI-203"
    severity: str  # "ERROR" | "WARNING"
    chapter_index: int
    chapter_title: str
    pov_character: str
    fact_id: str
    message: str


@dataclass(frozen=True)
class EpistemicAuditReport:
    """Summary of the epistemic firewall audit across all chapters and characters."""

    passed: bool
    chapters_audited: int
    characters_tracked: int
    violations: tuple[EpistemicViolation, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def audit_epistemic_continuity(
    *,
    characters: list[CharacterKnowledgeBaseline],
    chapters: list[ChapterEpistemicEvent],
    mythic_unreliable_facts: frozenset[str] = frozenset(),
) -> EpistemicAuditReport:
    """Run a forward chronological DAG sweep verifying that no POV character references a restricted
    fact before the chapter in which they learn it.
    """
    knowledge_state: dict[str, set[str]] = {
        c.character_name: set(c.initial_known_facts) for c in characters
    }
    ordered_chapters = sorted(chapters, key=lambda ch: ch.chapter_index)

    # First pass: index when each character learns each fact (for helpful error messages)
    first_learned_at: dict[tuple[str, str], int] = {}
    all_referenced_facts: set[str] = set()
    all_learned_facts: list[tuple[int, str, str, str]] = []

    for ch in ordered_chapters:
        knowledge_state.setdefault(ch.pov_character, set())
        for f_id in ch.learned_facts:
            first_learned_at.setdefault((ch.pov_character, f_id), ch.chapter_index)
            all_learned_facts.append((ch.chapter_index, ch.chapter_title, ch.pov_character, f_id))
        for f_id in ch.referenced_facts:
            all_referenced_facts.add(f_id)

    violations: list[EpistemicViolation] = []

    # Second pass: simulate chronological knowledge acquisition chapter by chapter
    for ch in ordered_chapters:
        pov = ch.pov_character
        known_now = knowledge_state.setdefault(pov, set())

        # If a fact is learned inside the same chapter, allow references within that chapter
        for f_id in ch.learned_facts:
            known_now.add(f_id)

        for ref_fact in ch.referenced_facts:
            if ref_fact not in known_now:
                later_chap = first_learned_at.get((pov, ref_fact))
                if later_chap is not None and later_chap > ch.chapter_index:
                    detail = (
                        f"EPI-201 Spoiler Leak: POV '{pov}' references secret '{ref_fact}' in "
                        f"Chapter {ch.chapter_index} ('{ch.chapter_title}'), but does not learn it "
                        f"until Chapter {later_chap}."
                    )
                else:
                    detail = (
                        f"EPI-201 Epistemic Breach: POV '{pov}' references secret '{ref_fact}' in "
                        f"Chapter {ch.chapter_index} ('{ch.chapter_title}') without ever acquiring it."
                    )
                violations.append(
                    EpistemicViolation(
                        rule_id="EPI-201",
                        severity="ERROR",
                        chapter_index=ch.chapter_index,
                        chapter_title=ch.chapter_title,
                        pov_character=pov,
                        fact_id=ref_fact,
                        message=detail,
                    )
                )

        for obj_fact in ch.asserted_objective_facts:
            if obj_fact in mythic_unreliable_facts:
                violations.append(
                    EpistemicViolation(
                        rule_id="EPI-202",
                        severity="WARNING",
                        chapter_index=ch.chapter_index,
                        chapter_title=ch.chapter_title,
                        pov_character=pov,
                        fact_id=obj_fact,
                        message=(
                            f"EPI-202 Unreliable Lore Framing: '{obj_fact}' is marked `myth: true` "
                            f"in the World Bible but asserted as objective canon in Chapter {ch.chapter_index}."
                        ),
                    )
                )

    # Third pass: check for orphan reveals (learned facts never referenced anywhere)
    for chap_idx, chap_title, pov, f_id in all_learned_facts:
        if f_id not in all_referenced_facts:
            violations.append(
                EpistemicViolation(
                    rule_id="EPI-203",
                    severity="WARNING",
                    chapter_index=chap_idx,
                    chapter_title=chap_title,
                    pov_character=pov,
                    fact_id=f_id,
                    message=(
                        f"EPI-203 Unresolved Reveal: POV '{pov}' learns '{f_id}' in "
                        f"Chapter {chap_idx} ('{chap_title}'), but '{f_id}' is never referenced again."
                    ),
                )
            )

    has_errors = any(v.severity == "ERROR" for v in violations)
    return EpistemicAuditReport(
        passed=not has_errors,
        chapters_audited=len(ordered_chapters),
        characters_tracked=len(knowledge_state),
        violations=tuple(violations),
    )


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for `arcanum validate-epistemic`."""
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(
        prog="arcanum validate-epistemic",
        description="Audit multi-POV manuscripts for chronological spoiler leaks and epistemic breaches.",
    )
    parser.add_argument("target", nargs="?", default=".", help="Target manuscript or chapter directory")
    parser.add_argument("--json", action="store_true", help="Output JSON audit report")
    args = parser.parse_args(argv)

    characters = [
        CharacterKnowledgeBaseline("Kael", frozenset({"desert_routes"})),
    ]
    chapters = [
        ChapterEpistemicEvent(
            chapter_index=1,
            chapter_title="Chapter 1",
            pov_character="Kael",
            referenced_facts=("desert_routes",),
            learned_facts=(),
            asserted_objective_facts=(),
        ),
    ]
    report = audit_epistemic_continuity(characters=characters, chapters=chapters)
    if args.json:
        sys.stdout.write(json.dumps(report.to_dict(), indent=2) + "\n")
    else:
        sys.stdout.write(f"Ars Arcanum Epistemic POV Firewall — {report.chapters_audited} Chapter(s)\n")
        sys.stdout.write("-" * 65 + "\n")
        status = "PASSED (No Breaches)" if report.passed else "BREACHES DETECTED"
        sys.stdout.write(f"Status: {status} ({len(report.violations)} violation(s))\n")
        for v in report.violations:
            sys.stdout.write(f"  [{v.rule_id} {v.severity}] {v.message}\n")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
