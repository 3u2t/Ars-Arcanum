#!/usr/bin/env python3
"""
Ars Arcanum Unified YAML Frontmatter Engine & Publishing Builder (src/arcanum/core/frontmatter.py)
===================================================================================================
High-performance, pure-Python standard library YAML frontmatter parser, extractor,
serializer, and modular front/back publishing matter generator.

Capabilities:
1. YAML Frontmatter Parsing & Coercion:
   - Safe zero-dependency recursive parsing of YAML headers, nested dicts, lists, and block scalars
   - Document and frontmatter parsing (`parse_yaml_frontmatter`, `parse_yaml_document`)
   - Strict frontmatter syntax verification (`parse_frontmatter`)
   - Serialization to standard YAML format (`serialize_yaml_document`, `serialize_yaml_frontmatter`, `dump_frontmatter`)
   - Splitting content into metadata dict and body markdown (`extract_frontmatter_and_body`)
2. Modular Front & Back Matter Publishing Builder (PUB-103):
   - Front matter generation: 01_Half_Title.md, 02_Title_Page.md, 03_Copyright.md, 04_Dedication.md, 05_Epigraph.md
   - Back matter generation: 01_Acknowledgments.md, 02_About_the_Author.md, 03_Also_By.md, 04_Discussion_Questions.md, 05_Reader_CTA.md
   - Atomic scaffolding with skip/force overwrite guarantees and scope awareness.

100% Sovereign Offline Architecture — Zero Pip Dependencies.
"""

from __future__ import annotations

import argparse
import datetime
import json
import logging
from pathlib import Path
import re
import sys
from typing import Any

from src.arcanum.core.scope import (
    add_scope_arguments,
    format_scope_banner,
    parse_scope_args,
    resolve_manuscript_dir,
)
from src.arcanum.core.storage import atomic_write

logger = logging.getLogger("arcanum.core.frontmatter")

FRONTMATTER_DELIM: str = "---"
FRONTMATTER_REGEX: re.Pattern[str] = re.compile(r"^---\s*\r?\n(.*?)\r?\n---\s*(?:\r?\n|$)", re.DOTALL)


# =============================================================================
# 1. Scalar Coercion & Splitting Primitives
# =============================================================================


def _coerce_scalar(val: str) -> Any:
    """Coerces a string scalar to int, float, bool, null, or unquoted string."""
    stripped = val.strip()
    if not stripped:
        return ""

    # Quoted strings
    if (stripped.startswith('"') and stripped.endswith('"')) or (stripped.startswith("'") and stripped.endswith("'")):
        inner = stripped[1:-1]
        # Unescape standard double quote escapes if double-quoted
        if stripped.startswith('"'):
            inner = inner.replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t').replace('\\\\', '\\')
        return inner

    lower = stripped.lower()
    if lower == "true":
        return True
    if lower == "false":
        return False
    if lower in ("none", "null", "~"):
        return None

    # Integer (including signed)
    if re.match(r"^[+-]?\d+$", stripped):
        try:
            return int(stripped)
        except ValueError:
            pass

    # Float (including scientific notation)
    if re.match(r"^[+-]?\d+\.\d+$", stripped) or re.match(r"^[+-]?\d+(?:\.\d+)?[eE][+-]?\d+$", stripped):
        try:
            return float(stripped)
        except ValueError:
            pass

    # Inline List [a, b, c]
    if stripped.startswith("[") and stripped.endswith("]"):
        inner = stripped[1:-1].strip()
        if not inner:
            return []
        items = []
        for part in _split_comma_preserving_quotes(inner):
            items.append(_coerce_scalar(part.strip()))
        return items

    # Inline Dict {a: 1, b: 2}
    if stripped.startswith("{") and stripped.endswith("}"):
        inner = stripped[1:-1].strip()
        if not inner:
            return {}
        d: dict[str, Any] = {}
        for part in _split_comma_preserving_quotes(inner):
            if ":" in part:
                k, v = part.split(":", 1)
                d[k.strip().strip("\"'")] = _coerce_scalar(v.strip())
        return d

    return stripped


def _split_comma_preserving_quotes(text: str) -> list[str]:
    """Splits a comma-delimited string while respecting nested quotes, brackets, and braces."""
    parts = []
    current: list[str] = []
    in_single = False
    in_double = False
    depth = 0

    for ch in text:
        if ch == "'" and not in_double:
            in_single = not in_single
            current.append(ch)
        elif ch == '"' and not in_single:
            in_double = not in_double
            current.append(ch)
        elif ch in ("[", "{") and not in_single and not in_double:
            depth += 1
            current.append(ch)
        elif ch in ("]", "}") and not in_single and not in_double:
            depth = max(0, depth - 1)
            current.append(ch)
        elif ch == "," and not in_single and not in_double and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)

    if current:
        parts.append("".join(current))
    return [p.strip() for p in parts if p.strip()]


# =============================================================================
# 2. Recursive YAML Parser
# =============================================================================


def _parse_yaml_recursive(lines: list[str], start_idx: int = 0, base_indent: int = 0) -> tuple[Any, int]:
    """
    Recursively parses indented YAML lines starting at start_idx into dicts, lists, or scalars.
    Returns (parsed_structure, next_line_index).
    """
    n = len(lines)
    i = start_idx

    # Determine whether current block is a list or dict
    # Peek at first non-empty, non-comment line
    is_list_block = False
    while i < n:
        raw = lines[i]
        stripped = raw.strip()
        if stripped and not stripped.startswith("#"):
            indent = len(raw) - len(raw.lstrip(" "))
            if indent < base_indent:
                # Lower indent -> return empty
                return {}, i
            if stripped.startswith("- ") or stripped == "-":
                is_list_block = True
            break
        i += 1

    if i >= n:
        return {}, n

    if is_list_block:
        result_list: list[Any] = []
        while i < n:
            raw = lines[i]
            stripped = raw.strip()
            if not stripped or stripped.startswith("#"):
                i += 1
                continue

            indent = len(raw) - len(raw.lstrip(" "))
            if indent < base_indent:
                break

            if stripped.startswith("- ") or stripped == "-":
                item_content = stripped[2:].strip() if stripped.startswith("- ") else ""
                child_indent = indent + 2

                is_quoted = (item_content.startswith('"') and item_content.endswith('"')) or (item_content.startswith("'") and item_content.endswith("'"))
                is_mapping = not is_quoted and ":" in item_content and not item_content.startswith(("[", "{"))

                # Check if item is an unquoted key-value mapping on same line (e.g. "- name: Gold")
                if is_mapping:
                    k, v = item_content.split(":", 1)
                    k = k.strip().strip("\"'")
                    v = v.strip()
                    sub_dict: dict[str, Any] = {}
                    if v:
                        sub_dict[k] = _coerce_scalar(v)
                    else:
                        sub_val, sub_next = _parse_yaml_recursive(lines, i + 1, child_indent)
                        sub_dict[k] = sub_val
                        i = sub_next
                        result_list.append(sub_dict)
                        continue

                    # Consume further keys for this list item at child_indent
                    i += 1
                    while i < n:
                        next_raw = lines[i]
                        next_strip = next_raw.strip()
                        if not next_strip or next_strip.startswith("#"):
                            i += 1
                            continue
                        next_indent = len(next_raw) - len(next_raw.lstrip(" "))
                        if next_indent < child_indent or next_strip.startswith("- "):
                            break
                        if ":" in next_strip:
                            nk, nv = next_strip.split(":", 1)
                            nk = nk.strip().strip("\"'")
                            nv = nv.strip()
                            if nv:
                                sub_dict[nk] = _coerce_scalar(nv)
                                i += 1
                            else:
                                n_val, n_next = _parse_yaml_recursive(lines, i + 1, next_indent + 2)
                                sub_dict[nk] = n_val
                                i = n_next
                        else:
                            i += 1
                    result_list.append(sub_dict)
                    continue

                if item_content:
                    result_list.append(_coerce_scalar(item_content))
                    i += 1
                else:
                    # Item content is indented on next lines
                    sub_val, sub_next = _parse_yaml_recursive(lines, i + 1, child_indent)
                    result_list.append(sub_val)
                    i = sub_next
            else:
                # Unexpected line at list level
                break
        return result_list, i

    # Dictionary block
    result_dict: dict[str, Any] = {}
    while i < n:
        raw = lines[i]
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        indent = len(raw) - len(raw.lstrip(" "))
        if indent < base_indent:
            break

        # Handle list item encountered inside dictionary (e.g. root dash or loose list)
        if stripped.startswith("- ") or stripped == "-":
            if not result_dict:
                sub_list, sub_next = _parse_yaml_recursive(lines, i, indent)
                return sub_list, sub_next
            i += 1
            continue

        if ":" in stripped:
            key, val = stripped.split(":", 1)
            key = key.strip().strip("\"'")
            val = val.strip()

            if val in ("|", "|-", "|+", ">", ">-", ">+"):
                # Multi-line block scalar
                scalar_lines = []
                block_indent = None
                is_folded = val.startswith(">")
                i += 1
                while i < n:
                    b_raw = lines[i]
                    b_strip = b_raw.strip()
                    if not b_strip:
                        scalar_lines.append("")
                        i += 1
                        continue
                    b_indent = len(b_raw) - len(b_raw.lstrip(" "))
                    if block_indent is None:
                        if b_indent <= indent:
                            break
                        block_indent = b_indent
                    elif b_indent < block_indent:
                        break
                    scalar_lines.append(b_raw[block_indent:] if len(b_raw) >= block_indent else b_strip)
                    i += 1
                if is_folded:
                    result_dict[key] = " ".join(scalar_lines).strip()
                else:
                    result_dict[key] = "\n".join(scalar_lines).strip()
                continue

            if val:
                result_dict[key] = _coerce_scalar(val)
                i += 1
            else:
                # Key with empty value -> check if followed by nested block or list
                sub_indent = indent + 1
                if i + 1 < n:
                    peek_raw = lines[i + 1]
                    peek_strip = peek_raw.strip()
                    if peek_strip and not peek_strip.startswith("#"):
                        peek_indent = len(peek_raw) - len(peek_raw.lstrip(" "))
                        if peek_strip.startswith("- "):
                            sub_indent = min(indent, peek_indent)
                        elif peek_indent > indent:
                            sub_indent = peek_indent
                sub_val, sub_next = _parse_yaml_recursive(lines, i + 1, sub_indent)
                result_dict[key] = sub_val if (sub_val != {} or sub_next > i + 1) else ""
                i = sub_next
        else:
            i += 1

    return result_dict, i


def _parse_yaml_lines(lines: list[str]) -> dict[str, Any]:
    """Parses a list of YAML lines into a dictionary, supporting nested structures and lists."""
    res, _ = _parse_yaml_recursive(lines, 0, 0)
    if isinstance(res, dict):
        return res
    if isinstance(res, list):
        return {"items": res}
    return {}


def parse_yaml_frontmatter(content: str) -> dict[str, Any]:
    """
    Parses YAML frontmatter block from Markdown content into a dictionary.
    Supports key-value pairs, nested dictionaries, inline lists ([a, b]),
    bulleted lists (- item), lists of objects, block scalars, and scalar coercion.
    Returns an empty dict if no valid frontmatter is found.
    """
    fm_match = FRONTMATTER_REGEX.match(content)
    if not fm_match:
        return {}

    lines = fm_match.group(1).splitlines()
    return _parse_yaml_lines(lines)


def parse_yaml_document(content: str) -> dict[str, Any]:
    """
    Parses a YAML document (such as manuscript.yaml or world.yaml) or frontmatter block.
    """
    fm_match = FRONTMATTER_REGEX.match(content)
    if fm_match:
        return parse_yaml_frontmatter(content)

    lines = content.splitlines()
    if lines and lines[0].strip() == FRONTMATTER_DELIM:
        lines = lines[1:]
    if lines and lines[-1].strip() == FRONTMATTER_DELIM:
        lines = lines[:-1]

    return _parse_yaml_lines(lines)


def parse_frontmatter(text: str) -> tuple[dict[str, Any], bool]:
    """
    Strict subset parser returning (frontmatter_dict, success_boolean).
    Used by world_doctor for structural verification.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != FRONTMATTER_DELIM:
        return {}, True

    # Scan for closing delimiter
    closing_idx = -1
    for idx in range(1, len(lines)):
        if lines[idx].strip() == FRONTMATTER_DELIM:
            closing_idx = idx
            break

    if closing_idx == -1:
        # Unclosed frontmatter
        return {}, False

    fm_lines = lines[1:closing_idx]

    # Validate syntax of each line before full parse
    for raw in fm_lines:
        s = raw.strip()
        if not s or s.startswith(("#", "- ")):
            continue
        if ":" not in s:
            return {}, False

    try:
        fm = _parse_yaml_lines(fm_lines)
        return fm, True
    except Exception:
        return {}, False


# =============================================================================
# 3. YAML Serialization Primitives
# =============================================================================


def _serialize_scalar(val: Any) -> str:
    """Serializes a Python scalar into a standard YAML representation."""
    if val is None:
        return "null"
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, (int, float)):
        return str(val)
    s = str(val)
    if not s:
        return '""'
    # Check if quotes are required
    if any(c in s for c in (':', '#', '{', '}', '[', ']', ',', '&', '*', '?', '|', '-', '<', '>', '=', '!', '%', '@', '\\', '"', "'", '\n')):
        escaped = s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        return f'"{escaped}"'
    # Numeric lookalikes or boolean strings should be quoted
    if s.lower() in ("true", "false", "yes", "no", "null", "none", "~") or re.match(r"^[+-]?\d+(?:\.\d+)?$", s):
        return f'"{s}"'
    return s


def serialize_yaml_document(data: dict[str, Any], indent: int = 0) -> str:
    """Serializes a Python dictionary into a pure YAML document."""
    lines: list[str] = []
    prefix = "  " * indent

    for key, val in data.items():
        k_str = str(key)
        if isinstance(val, dict):
            if not val:
                lines.append(f"{prefix}{k_str}: {{}}")
            else:
                lines.append(f"{prefix}{k_str}:")
                nested = serialize_yaml_document(val, indent=indent + 1)
                lines.append(nested)
        elif isinstance(val, list):
            if not val:
                lines.append(f"{prefix}{k_str}: []")
            else:
                lines.append(f"{prefix}{k_str}:")
                for item in val:
                    if isinstance(item, dict):
                        # First key of dict on same line as hyphen
                        dict_lines = serialize_yaml_document(item, indent=indent + 2).splitlines()
                        if dict_lines:
                            first = dict_lines[0].lstrip()
                            lines.append(f"{prefix}  - {first}")
                            for rem in dict_lines[1:]:
                                lines.append(rem)
                        else:
                            lines.append(f"{prefix}  - {{}}")
                    elif isinstance(item, list):
                        lines.append(f"{prefix}  - {json.dumps(item)}")
                    else:
                        lines.append(f"{prefix}  - {_serialize_scalar(item)}")
        else:
            lines.append(f"{prefix}{k_str}: {_serialize_scalar(val)}")

    return "\n".join(lines)


def serialize_yaml_frontmatter(data: dict[str, Any], body: str = "") -> str:
    """Serializes metadata into fenced YAML frontmatter with markdown body."""
    yaml_str = serialize_yaml_document(data)
    if body:
        return f"---\n{yaml_str}\n---\n\n{body.lstrip()}"
    return f"---\n{yaml_str}\n---\n"


dump_frontmatter = serialize_yaml_frontmatter


def extract_frontmatter_and_body(content: str) -> tuple[dict[str, Any], str]:
    """Splits markdown content into frontmatter metadata dictionary and body text."""
    fm_match = FRONTMATTER_REGEX.match(content)
    if not fm_match:
        return {}, content

    fm_dict = parse_yaml_frontmatter(content)
    body = content[fm_match.end():]
    return fm_dict, body


# =============================================================================
# 4. Modular Front & Back Matter Publishing Builder (PUB-103)
# =============================================================================


def generate_frontmatter_modules(metadata: dict[str, Any]) -> dict[str, str]:
    """Generates standard front matter Markdown documents."""
    title = metadata.get("title", "Untitled Novel")
    subtitle = metadata.get("subtitle", "")
    author = metadata.get("author", "Author Name")
    publisher = metadata.get("publisher", "Independent Publishing Press")
    year = metadata.get("copyright_year", str(datetime.date.today().year))
    isbn = metadata.get("isbn", "978-0-000000-00-0")
    edition = metadata.get("edition", "First Edition")
    dedication_text = metadata.get("dedication", "For those who dream among the stars and build worlds in the quiet dark.")
    epigraph_text = metadata.get("epigraph", "“The universe is not required to be in harmony with human ambition.”")
    epigraph_attr = metadata.get("epigraph_author", "Carl Sagan")

    half_title = f"# {title}\n"

    title_page = f"""# {title}

{'### ' + subtitle if subtitle else ''}

**{author}**

---

*{publisher}*
"""

    copyright_page = f"""# Copyright

Copyright © {year} by {author}
All rights reserved.

Published by {publisher}
{edition}

No part of this publication may be reproduced, distributed, or transmitted in any form or by any means, including photocopying, recording, or other electronic or mechanical methods, without the prior written permission of the publisher, except in the case of brief quotations embodied in critical reviews and certain other noncommercial uses permitted by copyright law.

This book is a work of fiction. Names, characters, places, and incidents either are products of the author’s imagination or are used fictitiously. Any resemblance to actual persons, living or dead, events, or locales is entirely coincidental.

Paperback ISBN: {isbn}
Cover Design by: Studio Arcanum

Printed in the United States of America
"""

    dedication_page = f"""# Dedication

*{dedication_text}*
"""

    epigraph_page = f"""# Epigraph

*{epigraph_text}*

— **{epigraph_attr}**
"""

    return {
        "01_Half_Title.md": half_title,
        "02_Title_Page.md": title_page,
        "03_Copyright.md": copyright_page,
        "04_Dedication.md": dedication_page,
        "05_Epigraph.md": epigraph_page,
    }


def generate_backmatter_modules(metadata: dict[str, Any]) -> dict[str, str]:
    """Generates standard back matter Markdown documents."""
    title = metadata.get("title", "Untitled Novel")
    author = metadata.get("author", "Author Name")
    newsletter_url = metadata.get("newsletter_url", "https://authorwebsite.com/newsletter")
    website_url = metadata.get("website_url", "https://authorwebsite.com")

    acknowledgments = f"""# Acknowledgments

Writing *{title}* has been a monumental journey that could not have been completed in isolation.

First and foremost, thank you to my family and loved ones for their enduring patience and encouragement through long drafting hours and quiet revisions.

Immense gratitude to my early alpha and beta readers, whose sharp critiques and discerning eyes shaped these chapters into their truest form.

Finally, to every reader who picks up this story and walks alongside these characters: thank you for keeping sovereign storytelling alive.
"""

    about_the_author = f"""# About the Author

**{author}** is a novelist and worldbuilder passionate about immersive speculative fiction and sovereign storytelling.

When not crafting secondary worlds and charting celestial orbits, {author} enjoys hiking, historical research, and tinkering with open-source writing tools.

Connect with the author online:
- Website: [{website_url}]({website_url})
- Newsletter: [{newsletter_url}]({newsletter_url})
"""

    also_by = f"""# Also by {author}

### The Core Universe Series
1. *Book I: The Awakening*
2. *Book II: The Broken Crown*
3. *Book III: The Celestial Gate*

### Standalone Novels
- *Wanderers of the Void*
- *Echoes in Iron*
"""

    discussion_questions = """# Discussion Questions for Book Clubs

1. How did the opening status quo establish the protagonist's core internal flaw?
2. What role did the secondary world setting play in shaping the moral choices of the characters?
3. At the narrative midpoint, how did the shift from reactive survival to proactive resistance change the group dynamics?
4. Which faction's ideological stance did you find most compelling, and why?
5. Did the resolution provide a satisfying emotional transformation for the central protagonist?
"""

    reader_cta = f"""# A Note from the Author

Thank you for reading *{title}*!

If you enjoyed this journey, please consider leaving a brief review on your favorite book platform. Reviews are the lifeblood of independent authors and help fellow readers discover new worlds.

### Join the Sovereign Reader Circle
Get exclusive bonus epilogues, high-resolution world maps, and advance reader copies of upcoming releases:

👉 **[{newsletter_url}]({newsletter_url})**
"""

    return {
        "01_Acknowledgments.md": acknowledgments,
        "02_About_the_Author.md": about_the_author,
        "03_Also_By.md": also_by,
        "04_Discussion_Questions.md": discussion_questions,
        "05_Reader_CTA.md": reader_cta,
    }


def scaffold_matter(manuscript_path: Path, metadata: dict[str, Any], force: bool = False) -> dict[str, Any]:
    """Writes modular front matter and back matter into manuscript directories using atomic writes."""
    front_matter_dir = manuscript_path / "00_Front_Matter"
    back_matter_dir = manuscript_path / "04_Back_Matter"

    front_matter_dir.mkdir(parents=True, exist_ok=True)
    back_matter_dir.mkdir(parents=True, exist_ok=True)

    front_files = generate_frontmatter_modules(metadata)
    back_files = generate_backmatter_modules(metadata)

    created = []
    skipped = []

    for name, content in front_files.items():
        fp = front_matter_dir / name
        if fp.is_file() and not force:
            skipped.append(str(fp))
        else:
            atomic_write(fp, content)
            created.append(str(fp))

    for name, content in back_files.items():
        fp = back_matter_dir / name
        if fp.is_file() and not force:
            skipped.append(str(fp))
        else:
            atomic_write(fp, content)
            created.append(str(fp))

    return {
        "target": str(manuscript_path),
        "created_count": len(created),
        "skipped_count": len(skipped),
        "created": created,
        "skipped": skipped,
    }


def main_matter(argv: list[str] | None = None) -> int:
    """CLI entrypoint for modular front & back matter builder."""
    parser = argparse.ArgumentParser(description="Ars Arcanum Modular Front & Back Matter Builder (PUB-103)")
    subparsers = parser.add_subparsers(dest="command", help="Command mode")

    p_build = subparsers.add_parser("build", help="Scaffold front & back matter into manuscript")
    p_build.add_argument("target", nargs="?", default=".", help="Manuscript directory path")
    p_build.add_argument("--title", help="Novel title")
    p_build.add_argument("--author", help="Author name")
    p_build.add_argument("--isbn", help="ISBN-13 number")
    p_build.add_argument("--year", help="Copyright year")
    p_build.add_argument("--publisher", help="Publisher imprint")
    p_build.add_argument("-f", "--force", action="store_true", help="Overwrite existing matter files")
    p_build.add_argument("--json", action="store_true", help="Output JSON results")
    add_scope_arguments(p_build)

    args = parser.parse_args(argv)

    if not args.command or args.command != "build":
        parser.print_help()
        if argv is None:
            sys.exit(0)
        return 0

    scope_obj = parse_scope_args(args)
    if args.target:
        p_cand = Path(args.target)
        if p_cand.exists():
            target_path = p_cand
        else:
            r_str = resolve_manuscript_dir(args.target, scope=scope_obj)
            if r_str and Path(r_str).is_dir():
                target_path = Path(r_str)
            else:
                print(f"Error: Target path does not exist: {args.target}", file=sys.stderr)
                if argv is None:
                    sys.exit(1)
                return 1
    else:
        r_str = resolve_manuscript_dir(scope=scope_obj)
        if r_str and Path(r_str).is_dir():
            target_path = Path(r_str)
        else:
            print("Error: No valid manuscript directory specified or discovered.", file=sys.stderr)
            if argv is None:
                sys.exit(1)
            return 1

    meta = {
        "title": target_path.name.replace("_", " "),
        "author": "Author Name",
        "isbn": "978-0-000000-00-0",
        "copyright_year": str(datetime.date.today().year),
        "publisher": "Ars Arcanum Press",
    }

    # If manuscript.yaml exists, read it
    manifest_path = target_path / "manuscript.yaml"
    if manifest_path.is_file():
        for line in manifest_path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if ":" in line and not line.startswith("#"):
                k, v = line.split(":", 1)
                k = k.strip().lower()
                v = v.strip().strip('"\'')
                if v:
                    meta[k] = v

    # Explicit CLI arguments always override defaults / manifest
    if args.title:
        meta["title"] = args.title
    if args.author:
        meta["author"] = args.author
    if args.isbn:
        meta["isbn"] = args.isbn
    if args.year:
        meta["copyright_year"] = args.year
    if args.publisher:
        meta["publisher"] = args.publisher

    res = scaffold_matter(target_path, meta, force=args.force)

    if args.json:
        print(json.dumps(res, indent=2))
        return 0

    print(format_scope_banner("Modular Front & Back Matter Scaffolder", scope_obj))
    print(f"Target Manuscript: {target_path.name}")
    print(f"Created: {res['created_count']} files | Skipped (already exist): {res['skipped_count']} files")
    print("-" * 65)
    for c in res["created"]:
        print(f"  ✓ Created: {Path(c).relative_to(target_path)}")
    for s in res["skipped"]:
        print(f"  · Exists (use --force to overwrite): {Path(s).relative_to(target_path)}")

    return 0


__all__ = [
    "FRONTMATTER_DELIM",
    "FRONTMATTER_REGEX",
    "_coerce_scalar",
    "_parse_yaml_lines",
    "_serialize_scalar",
    "_split_comma_preserving_quotes",
    "dump_frontmatter",
    "extract_frontmatter_and_body",
    "generate_backmatter_modules",
    "generate_frontmatter_modules",
    "main_matter",
    "parse_frontmatter",
    "parse_yaml_document",
    "parse_yaml_frontmatter",
    "scaffold_matter",
    "serialize_yaml_document",
    "serialize_yaml_frontmatter",
]


if __name__ == "__main__":
    sys.exit(main_matter())
