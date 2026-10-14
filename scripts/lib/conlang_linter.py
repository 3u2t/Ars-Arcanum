"""PolyGlot Conlang Lexicon Importer, Phonotactic Linter & Glossary Compiler (`arcanum conlang check`).

Bridges external conlang tools like PolyGlot (`.pgd` ZIP/XML dictionaries or raw `.xml` exports)
with Ars Arcanum's `Languages/` World Bible directory and `configs/plugins/speculative_naming/`:
1. Zero-Dependency PolyGlot Importer (`import_polyglot_lexicon`):
   - Reads `.pgd` archives (which package `PGDictionary.xml` inside a standard ZIP container)
     or standalone XML files using stdlib `zipfile` and `xml.etree.ElementTree`.
2. Phonotactic & Syllable Structure Validator (`CON-401` & `CON-402`):
   - Validates coined proper nouns and in-manuscript conlang phrases against user-defined phoneme
     inventories (consonants `C`, vowels `V`, liquids `L`, sibilants `S`) and banned clusters.
3. Omnibus Pronunciation Appendix Generator (`compile_glossary_markdown`):
   - Produces a sorted Markdown pronunciation and etymology table ready for `omnibus.py`.

Repository Target: `scripts/lib/conlang_linter.py`
Reference: https://github.com/aryansinghnagar/Ars-Arcanum
"""

from __future__ import annotations

import itertools
import re
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ConlangLexeme:
    """Single word entry in a constructed language lexicon."""

    con_word: str
    local_gloss: str
    pronunciation: str = ""
    part_of_speech: str = "noun"
    etymology: str = ""


@dataclass(frozen=True)
class PhonotacticSpec:
    """Phonotactic constraints for a constructed language in `Languages/<Conlang>.yaml`."""

    language_name: str
    allowed_consonants: tuple[str, ...] = ("p", "t", "k", "s", "m", "n", "l", "r", "w", "j", "d", "b", "g")
    allowed_vowels: tuple[str, ...] = ("a", "e", "i", "o", "u")
    banned_clusters: tuple[str, ...] = ()
    allow_vowel_hiatus: bool = False
    require_vowel_nucleus: bool = True


@dataclass(frozen=True)
class ConlangViolation:
    """Phonotactic or lexicon compliance violation."""

    rule_id: str  # "CON-401" | "CON-402"
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

    root = ET.fromstring(xml_bytes)  # noqa: S314
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

    # Tokenize word greedily into multi-character or single-character graphemes
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
        for prev_t, curr_t in itertools.pairwise(tokens):
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
    """CLI entrypoint for `arcanum conlang-check`."""
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(
        prog="arcanum conlang-check",
        description="Audit manuscript coined words against phonotactic rules or import PolyGlot dictionaries.",
    )
    parser.add_argument("words_or_file", nargs="*", help="Words to check or path to .pgd/.xml dictionary")
    parser.add_argument("--import-pgd", type=Path, help="Path to PolyGlot .pgd archive or XML file to import")
    parser.add_argument("--glossary", type=Path, help="Export compiled Markdown glossary to file")
    parser.add_argument("--language", default="Standard Conlang", help="Language name")
    parser.add_argument("--json", action="store_true", help="Output JSON results")
    args = parser.parse_args(argv)

    if args.import_pgd or (args.words_or_file and Path(args.words_or_file[0]).suffix in (".pgd", ".xml")):
        file_path = args.import_pgd or Path(args.words_or_file[0])
        lexemes = import_polyglot_lexicon(file_path)
        glossary_md = compile_glossary_markdown(args.language, lexemes)
        if args.glossary:
            args.glossary.write_text(glossary_md, encoding="utf-8")
            sys.stdout.write(f"✓ Exported {len(lexemes)} lexemes to {args.glossary}\n")
        elif args.json:
            sys.stdout.write(json.dumps([asdict(item) for item in lexemes], indent=2) + "\n")
        else:
            sys.stdout.write(f"✓ Imported {len(lexemes)} lexemes from {file_path.name}\n\n")
            sys.stdout.write(glossary_md)
        return 0

    words = args.words_or_file or ["sample", "word"]
    spec = PhonotacticSpec(language_name=args.language)
    res = audit_conlang_terms(words, spec)
    if args.json:
        sys.stdout.write(json.dumps(res, indent=2) + "\n")
    else:
        sys.stdout.write(f"Ars Arcanum Conlang Linter — {args.language}\n")
        sys.stdout.write("-" * 50 + "\n")
        status = "PASSED" if res["passed"] else "VIOLATIONS FOUND"
        sys.stdout.write(f"Checked {res['words_checked']} word(s): {status}\n")
        for v in res["violations"]:
            sys.stdout.write(f"  [{v['rule_id']}] {v['message']}\n")
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
