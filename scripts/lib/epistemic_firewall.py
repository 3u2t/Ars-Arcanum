"""Epistemic POV & Spoiler Firewall Engine for Ars Arcanum (`arcanum validate-epistemic`).

Models Epistemic Asymmetry across a multi-POV manuscript and its linked World Bible:
- Tracks what each character knows at baseline (`Characters/<Name>.md` frontmatter `knows: [...]`).
- Tracks chapter-ordered scene transitions (`chapter`, `pov`, `learns: [...]`, `references: [...]`,
  and wikilinks `[[Entity]]` mapped to secret lore IDs).
- Flags deterministic epistemic violations (`EPI-201` through `EPI-203`).

Repository Target: `scripts/lib/epistemic_firewall.py`
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import sys
from typing import Any

try:
    from lib.vault_index import VaultIndex
except ImportError:
    from vault_index import VaultIndex


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

    rule_id: str
    severity: str
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

    for ch in ordered_chapters:
        pov = ch.pov_character
        known_now = knowledge_state.setdefault(pov, set())

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


def _as_str_tuple(raw: Any) -> tuple[str, ...]:
    if isinstance(raw, (list, tuple)):
        return tuple(str(x).strip() for x in raw if str(x).strip())
    if isinstance(raw, str) and raw.strip():
        return tuple(s.strip() for s in raw.split(",") if s.strip())
    return ()


def audit_vault_epistemic(vault_root: Path) -> EpistemicAuditReport:
    """Automatically scan a Sovereign Vault via `VaultIndex` and run the Epistemic POV Firewall."""
    index = VaultIndex(vault_root)
    nodes = index.scan_vault()

    characters: list[CharacterKnowledgeBaseline] = []
    chapters: list[ChapterEpistemicEvent] = []
    myths: set[str] = set()

    for idx_num, node in enumerate(nodes, start=1):
        fm = node.frontmatter
        rel = node.relative_path

        if fm.get("myth") is True or fm.get("unreliable") is True:
            fact_id = str(fm.get("fact_id") or Path(rel).stem)
            myths.add(fact_id)

        if "Characters/" in rel or fm.get("type") == "character":
            char_name = str(fm.get("name") or fm.get("title") or Path(rel).stem)
            knows = frozenset(_as_str_tuple(fm.get("knows", [])))
            characters.append(CharacterKnowledgeBaseline(character_name=char_name, initial_known_facts=knows))
        elif "chapter" in fm or "pov" in fm or "pov" in node.directives:
            chap_idx = int(fm.get("chapter", idx_num))
            chap_title = str(fm.get("title") or Path(rel).stem)
            pov = str(fm.get("pov") or node.directives.get("pov") or "Omniscient")
            refs = _as_str_tuple(fm.get("references", []))
            learned = _as_str_tuple(fm.get("learns") or fm.get("reveals") or [])
            asserted = _as_str_tuple(fm.get("asserts", []))
            chapters.append(
                ChapterEpistemicEvent(
                    chapter_index=chap_idx,
                    chapter_title=chap_title,
                    pov_character=pov,
                    referenced_facts=refs,
                    learned_facts=learned,
                    asserted_objective_facts=asserted,
                )
            )

    return audit_epistemic_continuity(
        characters=characters,
        chapters=chapters,
        mythic_unreliable_facts=frozenset(myths),
    )


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for `arcanum validate-epistemic` / `arcanum epistemic`."""
    parser = argparse.ArgumentParser(
        prog="arcanum validate-epistemic",
        description="Audit a Sovereign Vault or Manuscript for POV spoiler leaks and epistemic breaches.",
    )
    parser.add_argument("vault", nargs="?", type=Path, default=Path.cwd(), help="Vault or manuscript directory")
    args = parser.parse_args(argv)

    report = audit_vault_epistemic(args.vault)
    sys.stdout.write(json.dumps(report.to_dict(), indent=2) + "\n")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
