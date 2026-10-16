"""Bidirectional CriticMarkup <-> OpenXML Word Tracked Changes Bridge (Phase 3A Refactor).

Upgrades `scripts/lib/docx_builder.py` and `scripts/lib/docx_sync.py` with:
1. Pure `xml.etree.ElementTree` DOM construction for `word/document.xml`.
2. Full preservation of Microsoft Word Tracked Changes (`<w:ins>`, `<w:del>` / `<w:delText>`)
   and Editor Comments (`word/comments.xml` + `<w:commentReference>`).

Repository Target: `scripts/lib/docx_tracked_changes.py`
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET  # nosec B405
import zipfile

try:
    from lib.vault_index import PathSecurityError, atomic_write, is_safe_subpath
except ImportError:
    from vault_index import PathSecurityError, atomic_write, is_safe_subpath

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
ET.register_namespace("w", W_NS)

_CRITIC_TOKEN_RE = re.compile(
    r"(\{\+\+(?P<ins>.*?)\+\+\}"
    r"|\{--(?P<del>.*?)--\}"
    r"|\{~~(?P<sub_old>.*?)~>(?P<sub_new>.*?)~~\}"
    r"|\{>>(?P<comment>.*?)<<\})",
    re.DOTALL,
)


def _w(tag: str) -> str:
    return f"{{{W_NS}}}{tag}"


def build_tracked_document_xml(
    markdown_body: str,
    *,
    author: str = "Ars Arcanum Author",
    timestamp: str | None = None,
) -> tuple[bytes, bytes]:
    """Construct `word/document.xml` and `word/comments.xml` via `xml.etree.ElementTree` DOM nodes."""
    iso_ts = timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    doc_root = ET.Element(_w("document"))
    body_el = ET.SubElement(doc_root, _w("body"))

    comments_root = ET.Element(_w("comments"))
    rev_id = 1
    comment_id = 1

    paragraphs = [p.strip() for p in re.split(r"\r?\n\s*\r?\n", markdown_body) if p.strip()]
    for para_text in paragraphs:
        p_el = ET.SubElement(body_el, _w("p"))

        if para_text.startswith("#"):
            level = len(para_text) - len(para_text.lstrip("#"))
            clean_heading = para_text.lstrip("#").strip()
            p_pr = ET.SubElement(p_el, _w("pPr"))
            p_style = ET.SubElement(p_pr, _w("pStyle"))
            p_style.set(_w("val"), f"Heading{min(level, 6)}")
            r_el = ET.SubElement(p_el, _w("r"))
            t_el = ET.SubElement(r_el, _w("t"))
            t_el.text = clean_heading
            continue

        cursor = 0
        for match in _CRITIC_TOKEN_RE.finditer(para_text):
            start, end = match.span()
            if start > cursor:
                _append_text_run(p_el, para_text[cursor:start])

            if match.group("ins") is not None:
                ins_el = ET.SubElement(
                    p_el,
                    _w("ins"),
                    {_w("id"): str(rev_id), _w("author"): author, _w("date"): iso_ts},
                )
                rev_id += 1
                _append_text_run(ins_el, match.group("ins"))

            elif match.group("del") is not None:
                del_el = ET.SubElement(
                    p_el,
                    _w("del"),
                    {_w("id"): str(rev_id), _w("author"): author, _w("date"): iso_ts},
                )
                rev_id += 1
                _append_del_run(del_el, match.group("del"))

            elif match.group("sub_old") is not None:
                del_el = ET.SubElement(
                    p_el,
                    _w("del"),
                    {_w("id"): str(rev_id), _w("author"): author, _w("date"): iso_ts},
                )
                rev_id += 1
                _append_del_run(del_el, match.group("sub_old"))

                ins_el = ET.SubElement(
                    p_el,
                    _w("ins"),
                    {_w("id"): str(rev_id), _w("author"): author, _w("date"): iso_ts},
                )
                rev_id += 1
                _append_text_run(ins_el, match.group("sub_new") or "")

            elif match.group("comment") is not None:
                raw_comment = match.group("comment").strip()
                c_author = author
                c_body = raw_comment
                if ":" in raw_comment:
                    maybe_author, maybe_body = raw_comment.split(":", 1)
                    if len(maybe_author.strip()) <= 40:
                        c_author = maybe_author.strip()
                        c_body = maybe_body.strip()

                cid_str = str(comment_id)
                comment_id += 1
                r_ref = ET.SubElement(p_el, _w("r"))
                ET.SubElement(r_ref, _w("commentReference"), {_w("id"): cid_str})

                c_el = ET.SubElement(
                    comments_root,
                    _w("comment"),
                    {_w("id"): cid_str, _w("author"): c_author, _w("date"): iso_ts},
                )
                cp_el = ET.SubElement(c_el, _w("p"))
                _append_text_run(cp_el, c_body)

            cursor = end

        if cursor < len(para_text):
            _append_text_run(p_el, para_text[cursor:])

    doc_bytes = ET.tostring(doc_root, encoding="utf-8", xml_declaration=True)
    comments_bytes = ET.tostring(comments_root, encoding="utf-8", xml_declaration=True)
    return doc_bytes, comments_bytes


def _append_text_run(parent: ET.Element, text: str) -> None:
    if not text:
        return
    r_el = ET.SubElement(parent, _w("r"))
    t_el = ET.SubElement(r_el, _w("t"))
    if text.startswith(" ") or text.endswith(" "):
        t_el.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    t_el.text = text


def _append_del_run(parent: ET.Element, text: str) -> None:
    if not text:
        return
    r_el = ET.SubElement(parent, _w("r"))
    dt_el = ET.SubElement(r_el, _w("delText"))
    if text.startswith(" ") or text.endswith(" "):
        dt_el.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    dt_el.text = text


def export_markdown_to_docx(
    markdown_body: str,
    output_docx: Path,
    *,
    vault_root: Path | None = None,
    author: str = "Ars Arcanum Author",
) -> Path:
    """Package `markdown_body` (with CriticMarkup) into a valid `.docx` archive with OpenXML Tracked Changes."""
    resolved_out = output_docx.resolve()
    if vault_root is not None and not is_safe_subpath(vault_root, resolved_out):
        raise PathSecurityError(f"Output DOCX path escapes vault root: {resolved_out}")

    resolved_out.parent.mkdir(parents=True, exist_ok=True)
    doc_xml, comments_xml = build_tracked_document_xml(markdown_body, author=author)

    content_types_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '<Override PartName="/word/comments.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"/>'
        "</Types>"
    ).encode("utf-8")

    rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="word/document.xml"/>'
        "</Relationships>"
    ).encode("utf-8")

    with zipfile.ZipFile(resolved_out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types_xml)
        zf.writestr("_rels/.rels", rels_xml)
        zf.writestr("word/document.xml", doc_xml)
        zf.writestr("word/comments.xml", comments_xml)

    return resolved_out


def pull_docx_to_markdown(docx_path: Path, *, vault_root: Path | None = None) -> str:
    """Read an edited `.docx` archive and reconstruct Markdown with inline CriticMarkup."""
    resolved_in = docx_path.resolve()
    if vault_root is not None and not is_safe_subpath(vault_root, resolved_in):
        raise PathSecurityError(f"Input DOCX path escapes vault root: {resolved_in}")

    comments_map: dict[str, str] = {}
    with zipfile.ZipFile(resolved_in, "r") as zf:
        if "word/comments.xml" in zf.namelist():
            c_root = ET.fromstring(zf.read("word/comments.xml"))  # nosec B314
            for c_el in c_root.findall(_w("comment")):
                cid = c_el.get(_w("id"), "")
                c_author = c_el.get(_w("author"), "Editor")
                c_texts = [t.text or "" for t in c_el.iter(_w("t"))]
                comments_map[cid] = f"{c_author}: {''.join(c_texts).strip()}"

        doc_root = ET.fromstring(zf.read("word/document.xml"))  # nosec B314

    body_el = doc_root.find(_w("body"))
    if body_el is None:
        return ""

    out_paragraphs: list[str] = []
    for p_el in body_el.findall(_w("p")):
        heading_prefix = ""
        p_pr = p_el.find(_w("pPr"))
        if p_pr is not None:
            p_style = p_pr.find(_w("pStyle"))
            if p_style is not None:
                val = p_style.get(_w("val"), "")
                if val.startswith("Heading") and val[7:].isdigit():
                    heading_prefix = "#" * int(val[7:]) + " "

        fragments: list[str] = []
        for child in p_el:
            if child.tag == _w("r"):
                for sub in child:
                    if sub.tag == _w("t") and sub.text:
                        fragments.append(sub.text)
                    elif sub.tag == _w("commentReference"):
                        cid = sub.get(_w("id"), "")
                        if cid in comments_map:
                            fragments.append(f"{{>>{comments_map[cid]}<<}}")
            elif child.tag == _w("ins"):
                ins_text = "".join(t.text or "" for t in child.iter(_w("t")))
                if ins_text:
                    fragments.append(f"{{++{ins_text}++}}")
            elif child.tag == _w("del"):
                del_text = "".join(dt.text or "" for dt in child.iter(_w("delText")))
                if del_text:
                    fragments.append(f"{{--{del_text}--}}")

        para_str = "".join(fragments).strip()
        if para_str:
            out_paragraphs.append(f"{heading_prefix}{para_str}")

    return "\n\n".join(out_paragraphs) + ("\n" if out_paragraphs else "")


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for `arcanum docx-tracked`."""
    parser = argparse.ArgumentParser(
        prog="arcanum docx-tracked",
        description="Bidirectional Markdown CriticMarkup <-> Word Tracked Changes (.docx) converter.",
    )
    sub = parser.add_subparsers(dest="action", required=True)

    exp_p = sub.add_parser("export", help="Export Markdown with CriticMarkup to .docx with Tracked Changes")
    exp_p.add_argument("input_md", type=Path, help="Source Markdown file")
    exp_p.add_argument("output_docx", type=Path, help="Destination .docx file")
    exp_p.add_argument("--author", default="Ars Arcanum Author", help="Author name for tracked revisions")

    pull_p = sub.add_parser("pull", help="Pull .docx with Tracked Changes into Markdown with CriticMarkup")
    pull_p.add_argument("input_docx", type=Path, help="Source .docx file")
    pull_p.add_argument("output_md", nargs="?", type=Path, default=None, help="Optional destination Markdown file")

    args = parser.parse_args(argv)
    if args.action == "export":
        body = args.input_md.read_text(encoding="utf-8")
        out_path = export_markdown_to_docx(body, args.output_docx, author=args.author)
        sys.stdout.write(f"Exported Tracked Changes DOCX to {out_path}\n")
        return 0

    md_out = pull_docx_to_markdown(args.input_docx)
    if args.output_md is not None:
        atomic_write(args.output_md, md_out)
        sys.stdout.write(f"Pulled Tracked Changes Markdown to {args.output_md}\n")
    else:
        sys.stdout.write(md_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
