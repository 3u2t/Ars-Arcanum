"""PolyGlot Conlang Lexicon Importer, Phonotactic Linter & Glossary Compiler (src/arcanum/worldbible/conlang.py).

Bridges external conlang tools like PolyGlot (`.pgd` ZIP/XML dictionaries or raw `.xml` exports)
with Ars Arcanum's `Languages/` World Bible directory and `configs/plugins/speculative_naming/`.
Provides phonotactic constraint validation (`CON-401` & `CON-402`), markdown glossary compilation,
and air-gapped SVG etymological derivation trees.
"""

from __future__ import annotations

import argparse
import itertools
import json
from dataclasses import asdict, dataclass
from pathlib import Path
import re
import sys
from typing import Any
import zipfile

try:
    from scripts.lib.audit_hardening import parse_xml_safe_bytes, validate_safe_zip_archive
except ImportError:
    try:
        from lib.audit_hardening import parse_xml_safe_bytes, validate_safe_zip_archive
    except ImportError:
        import xml.etree.ElementTree as ET

        def parse_xml_safe_bytes(xml_bytes: bytes) -> ET.Element:
            return ET.fromstring(xml_bytes)  # nosec B314

        def validate_safe_zip_archive(path: Path) -> None:
            pass


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
        validate_safe_zip_archive(resolved)
        with zipfile.ZipFile(resolved, "r") as zf:
            xml_names = [n for n in zf.namelist() if n.endswith(".xml")]
            if not xml_names:
                raise ValueError(f"No XML dictionary found inside PolyGlot archive {resolved}")
            xml_bytes = zf.read(xml_names[0])
    else:
        xml_bytes = resolved.read_bytes()

    root = parse_xml_safe_bytes(xml_bytes)
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


def render_etymology_tree_svg(
    lexemes: list[ConlangLexeme],
    width: int = 800,
    height: int = 500,
    theme: str = "dark",
) -> str:
    """Renders an air-gapped SVG genealogical tree diagram of conlang lexical derivations."""
    is_light = (theme.lower() == "light")
    bg_color = "#ffffff" if is_light else "#0d1117"
    text_title = "#0969da" if is_light else "#58a6ff"
    text_header = "#59636e" if is_light else "#8b949e"
    guide_stroke = "#d0d7de" if is_light else "#30363d"

    leaf_bg = "#f6f8fa" if is_light else "#161b22"
    leaf_stroke = "#1a7f37" if is_light else "#238636"
    leaf_text = "#1a7f37" if is_light else "#3fb950"
    leaf_gloss_text = "#59636e" if is_light else "#8b949e"

    mid_bg = "#f6f8fa" if is_light else "#161b22"
    mid_stroke = "#8250df" if is_light else "#8957e5"
    mid_text = "#8250df" if is_light else "#d2a8ff"

    root_bg = "#eaeef2" if is_light else "#1f242c"
    root_stroke = "#0969da" if is_light else "#58a6ff"
    root_text = "#0969da" if is_light else "#58a6ff"

    conn_mid = guide_stroke
    conn_leaf = "#1a7f37" if is_light else "#238636"
    conn_direct = "#0969da" if is_light else "#1f6feb"

    if not lexemes:
        empty_fill = text_header
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
            f'width="{width}" height="{height}" style="background-color: {bg_color}; font-family: system-ui, -apple-system, sans-serif;">'
            f'<text x="50%" y="50%" fill="{empty_fill}" text-anchor="middle">No lexemes found</text></svg>'
        )

    chains: list[tuple[str, str, str, str, str]] = []
    for lx in lexemes:
        etym = lx.etymology.strip()
        if ">" in etym:
            steps = [s.strip() for s in etym.split(">") if s.strip()]
        elif "->" in etym:
            steps = [s.strip() for s in etym.split("->") if s.strip()]
        else:
            steps = [etym] if etym else [lx.con_word]

        root = steps[0]
        intermediate = steps[1] if len(steps) > 2 else (steps[0] if len(steps) == 2 else "")
        chains.append((root, intermediate, lx.con_word, lx.local_gloss, lx.part_of_speech))

    roots = sorted({c[0] for c in chains})
    row_height = max(50.0, (height - 80.0) / max(1, len(chains)))
    svg_height = max(height, int(len(chains) * row_height + 100))

    x_root = 130.0
    x_mid = 380.0
    x_leaf = 630.0

    elements: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {svg_height}" width="{width}" height="{svg_height}" style="background-color: {bg_color}; font-family: system-ui, -apple-system, sans-serif;">',
        "  <title>PolyGlot Conlang Etymology Tree</title>",
        f'  <text x="{width / 2.0}" y="30" text-anchor="middle" fill="{text_title}" font-size="16" font-weight="700">CONLANG ETYMOLOGICAL DERIVATION TREE</text>',
        "  <!-- Column Headers -->",
        f'  <text x="{x_root}" y="56" text-anchor="middle" fill="{text_header}" font-size="11" font-weight="600">PROTO-ROOT</text>',
        f'  <text x="{x_mid}" y="56" text-anchor="middle" fill="{text_header}" font-size="11" font-weight="600">HISTORICAL DIALECT</text>',
        f'  <text x="{x_leaf}" y="56" text-anchor="middle" fill="{text_header}" font-size="11" font-weight="600">DAUGHTER WORD &amp; GLOSS</text>',
    ]

    current_y = 85.0
    root_y_map: dict[str, float] = {}
    mid_y_map: dict[tuple[str, str], float] = {}

    for root in roots:
        root_chains = [c for c in chains if c[0] == root]
        root_start_y = current_y
        root_end_y = current_y + (len(root_chains) - 1) * row_height
        root_y_map[root] = (root_start_y + root_end_y) / 2.0

        for r, m, leaf, gloss, _pos in root_chains:
            mid_key = (r, m)
            if mid_key not in mid_y_map:
                mid_chains = [c for c in root_chains if c[1] == m]
                m_start_y = current_y
                m_end_y = current_y + (len(mid_chains) - 1) * row_height
                mid_y_map[mid_key] = (m_start_y + m_end_y) / 2.0

            ry = root_y_map[root]
            my = mid_y_map[mid_key] if m else ry
            leaf_y = current_y

            if m:
                elements.append(
                    f'  <path d="M {x_root + 55} {ry:.1f} C {x_root + 120} {ry:.1f}, {x_mid - 65} {my:.1f}, {x_mid - 55} {my:.1f}" '
                    f'fill="none" stroke="{conn_mid}" stroke-width="1.8" />'
                )
                elements.append(
                    f'  <path d="M {x_mid + 55} {my:.1f} C {x_mid + 120} {my:.1f}, {x_leaf - 75} {leaf_y:.1f}, {x_leaf - 65} {leaf_y:.1f}" '
                    f'fill="none" stroke="{conn_leaf}" stroke-width="1.8" />'
                )
            else:
                elements.append(
                    f'  <path d="M {x_root + 55} {ry:.1f} C {x_root + 150} {ry:.1f}, {x_leaf - 80} {leaf_y:.1f}, {x_leaf - 65} {leaf_y:.1f}" '
                    f'fill="none" stroke="{conn_direct}" stroke-width="1.8" />'
                )

            escaped_leaf = leaf.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            escaped_gloss = gloss.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            elements.append(
                f'  <g transform="translate({x_leaf}, {leaf_y})">'
                f'    <rect x="-65" y="-14" width="160" height="28" rx="6" fill="{leaf_bg}" stroke="{leaf_stroke}" stroke-width="1.5" />'
                f'    <text x="-55" y="4" fill="{leaf_text}" font-size="12" font-weight="700">{escaped_leaf}</text>'
                f'    <text x="85" y="4" text-anchor="end" fill="{leaf_gloss_text}" font-size="10">"{escaped_gloss}"</text>'
                f"  </g>"
            )
            current_y += row_height

    for (_r, m), my in mid_y_map.items():
        if m:
            escaped_m = m.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            elements.append(
                f'  <g transform="translate({x_mid}, {my:.1f})">'
                f'    <rect x="-55" y="-13" width="110" height="26" rx="5" fill="{mid_bg}" stroke="{mid_stroke}" stroke-width="1.2" />'
                f'    <text x="0" y="4" text-anchor="middle" fill="{mid_text}" font-size="11" font-weight="600">{escaped_m}</text>'
                f"  </g>"
            )

    for root, ry in root_y_map.items():
        escaped_root = root.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        elements.append(
            f'  <g transform="translate({x_root}, {ry:.1f})">'
            f'    <rect x="-60" y="-15" width="120" height="30" rx="6" fill="{root_bg}" stroke="{root_stroke}" stroke-width="1.8" />'
            f'    <text x="0" y="5" text-anchor="middle" fill="{root_text}" font-size="12" font-weight="700">*{escaped_root.lstrip("*")}</text>'
            f"  </g>"
        )

    elements.append("</svg>")
    return "\n".join(elements)


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


__all__ = [
    "ConlangLexeme",
    "ConlangViolation",
    "PhonotacticSpec",
    "audit_conlang_terms",
    "compile_glossary_markdown",
    "import_polyglot_lexicon",
    "main",
    "render_etymology_tree_svg",
    "validate_word_phonotactics",
]
