"""PolyGlot Conlang Lexicon Importer, Phonotactic Linter & Glossary Compiler (`arcanum conlang-check`).

Bridges external conlang tools like PolyGlot (`.pgd` ZIP/XML dictionaries or raw `.xml` exports)
with Ars Arcanum's `Languages/` World Bible directory and `configs/plugins/speculative_naming/`.

Repository Target: `scripts/lib/conlang_linter.py`
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from itertools import pairwise
import json
from pathlib import Path
import re
import sys
from typing import Any
import xml.etree.ElementTree as ET  # nosec B405
import zipfile


try:
    from src.arcanum.worldbible.conlang import ConlangLexeme, render_etymology_tree_svg
except ImportError:
    @dataclass(frozen=True)
    class ConlangLexeme:  # type: ignore[no-redef]
        """Single word entry in a constructed language lexicon."""

        con_word: str
        local_gloss: str
        pronunciation: str = ""
        part_of_speech: str = "noun"
        etymology: str = ""

    def render_etymology_tree_svg(  # type: ignore[no-redef]
        lexemes: list[ConlangLexeme],
        *,
        width: int = 800,
        height: int = 600,
        theme: str = "dark",
    ) -> str:
        return "<svg></svg>"


@dataclass(frozen=True)
class PhonotacticSpec:
    """Phonotactic constraints for a constructed language in `Languages/<Conlang>.yaml`."""

    language_name: str
    allowed_consonants: tuple[str, ...]
    allowed_vowels: tuple[str, ...]
    banned_clusters: tuple[str, ...] = ()
    allow_vowel_hiatus: bool = False
    require_vowel_nucleus: bool = True


@dataclass(frozen=True)
class ConlangViolation:
    """Phonotactic or lexicon compliance violation."""

    rule_id: str
    word: str
    language_name: str
    message: str


def import_polyglot_lexicon(source_path: Path) -> list[ConlangLexeme]:
    """Import a PolyGlot `.pgd` ZIP archive or XML dictionary without external dependencies."""
    resolved = source_path.resolve()
    if zipfile.is_zipfile(resolved):
        with zipfile.ZipFile(resolved, "r") as zf:
            xml_names = [n for n in zf.namelist() if n.endswith(".xml")]
            if not xml_names:
                raise ValueError(f"No XML dictionary found inside PolyGlot archive {resolved}")
            xml_bytes = zf.read(xml_names[0])
    else:
        xml_bytes = resolved.read_bytes()

    root = ET.fromstring(xml_bytes)  # nosec B314
    lexicon_node = root.find("lexicon")
    word_nodes = lexicon_node.findall("word") if lexicon_node is not None else root.findall(".//word")

    entries: list[ConlangLexeme] = []
    for w_el in word_nodes:
        con_word = (w_el.findtext("conWord") or "").strip()
        local_word = (w_el.findtext("localWord") or "").strip()
        pron = (w_el.findtext("proc") or w_el.findtext("pronunciation") or "").strip()
        pos = (w_el.findtext("wordTypeId") or w_el.findtext("partOfSpeech") or "noun").strip()
        etym = (w_el.findtext("etymology") or "").strip()
        if con_word:
            entries.append(
                ConlangLexeme(
                    con_word=con_word,
                    local_gloss=local_word,
                    pronunciation=pron,
                    part_of_speech=pos,
                    etymology=etym,
                )
            )
    return sorted(entries, key=lambda x: x.con_word.lower())


def validate_word_phonotactics(word: str, spec: PhonotacticSpec) -> list[ConlangViolation]:
    """Check whether `word` conforms to the phoneme inventory and cluster rules of `spec`."""
    cleaned = re.sub(r"['’\-]", "", word.strip().lower())
    if not cleaned:
        return []

    violations: list[ConlangViolation] = []
    all_graphemes = sorted(
        set(spec.allowed_consonants) | set(spec.allowed_vowels),
        key=len,
        reverse=True,
    )
    vowel_set = set(spec.allowed_vowels)

    idx = 0
    tokens: list[str] = []
    while idx < len(cleaned):
        matched_grapheme: str | None = None
        for g in all_graphemes:
            if cleaned.startswith(g, idx):
                matched_grapheme = g
                break
        if matched_grapheme is None:
            bad_char = cleaned[idx]
            violations.append(
                ConlangViolation(
                    rule_id="CON-401",
                    word=word,
                    language_name=spec.language_name,
                    message=(
                        f"CON-401 Illegal Phoneme: '{word}' contains grapheme '{bad_char}' outside "
                        f"the {spec.language_name} phoneme inventory."
                    ),
                )
            )
            idx += 1
        else:
            tokens.append(matched_grapheme)
            idx += len(matched_grapheme)

    if spec.require_vowel_nucleus and tokens and not any(t in vowel_set for t in tokens):
        violations.append(
            ConlangViolation(
                rule_id="CON-402",
                word=word,
                language_name=spec.language_name,
                message=f"CON-402 Missing Vowel Nucleus: '{word}' contains no valid vowel phoneme.",
            )
        )

    for cluster in spec.banned_clusters:
        if cluster.lower() in cleaned:
            violations.append(
                ConlangViolation(
                    rule_id="CON-402",
                    word=word,
                    language_name=spec.language_name,
                    message=(
                        f"CON-402 Banned Cluster: '{word}' contains prohibited phonotactic cluster "
                        f"'{cluster}' in {spec.language_name}."
                    ),
                )
            )

    if not spec.allow_vowel_hiatus:
        for prev_t, curr_t in pairwise(tokens):
            if prev_t in vowel_set and curr_t in vowel_set and prev_t != curr_t:
                violations.append(
                    ConlangViolation(
                        rule_id="CON-402",
                        word=word,
                        language_name=spec.language_name,
                        message=(
                            f"CON-402 Prohibited Vowel Hiatus: '{word}' places adjacent distinct "
                            f"vowels '{prev_t}{curr_t}' without an epenthetic consonant."
                        ),
                    )
                )
                break

    return violations


def compile_glossary_markdown(language_name: str, lexemes: list[ConlangLexeme]) -> str:
    """Compile a Markdown pronunciation and etymology appendix for `omnibus.py`."""
    lines = [
        f"## Appendix: {language_name} Lexicon & Pronunciation Guide",
        "",
        "| Term | Pronunciation (IPA) | Part of Speech | Translation / Gloss | Etymology |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ]
    for item in sorted(lexemes, key=lambda x: x.con_word.lower()):
        ipa = f"`/{item.pronunciation}/`" if item.pronunciation else "—"
        etym = item.etymology or "—"
        lines.append(
            f"| **{item.con_word}** | {ipa} | {item.part_of_speech} | {item.local_gloss} | {etym} |"
        )
    return "\n".join(lines) + "\n"


def audit_conlang_terms(words: list[str], spec: PhonotacticSpec) -> dict[str, Any]:
    """Batch-validate a list of manuscript proper nouns or phrases against `spec`."""
    all_violations: list[ConlangViolation] = []
    for w in words:
        all_violations.extend(validate_word_phonotactics(w, spec))
    return {
        "passed": len(all_violations) == 0,
        "language_name": spec.language_name,
        "words_checked": len(words),
        "violations": [asdict(v) for v in all_violations],
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for `arcanum conlang-check` / `arcanum conlang-linter`."""
    parser = argparse.ArgumentParser(
        prog="arcanum conlang-check",
        description="Validate constructed language terms or import a PolyGlot (.pgd/.xml) lexicon.",
    )
    parser.add_argument("--pgd", type=Path, default=None, help="Optional PolyGlot .pgd or .xml dictionary to import")
    parser.add_argument("--language", default="High Arcanum", help="Conlang name")
    parser.add_argument("--consonants", default="k,l,th,s,r,n,m,t,v,d,z", help="Comma-separated consonant inventory")
    parser.add_argument("--vowels", default="a,e,i,o,u", help="Comma-separated vowel inventory")
    parser.add_argument("--banned-clusters", default="sr,zt", help="Comma-separated banned clusters")
    parser.add_argument("words", nargs="*", help="Words to check against phonotactic rules")
    args = parser.parse_args(argv)

    spec = PhonotacticSpec(
        language_name=args.language,
        allowed_consonants=tuple(c.strip() for c in args.consonants.split(",") if c.strip()),
        allowed_vowels=tuple(v.strip() for v in args.vowels.split(",") if v.strip()),
        banned_clusters=tuple(b.strip() for b in args.banned_clusters.split(",") if b.strip()),
    )

    target_words = list(args.words)
    lexemes: list[ConlangLexeme] = []
    if args.pgd is not None and args.pgd.exists():
        lexemes = import_polyglot_lexicon(args.pgd)
        target_words.extend(lx.con_word for lx in lexemes)

    report = audit_conlang_terms(target_words, spec)
    if lexemes:
        report["imported_lexemes"] = len(lexemes)
        report["glossary_markdown"] = compile_glossary_markdown(args.language, lexemes)
    sys.stdout.write(json.dumps(report, indent=2) + "\n")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
