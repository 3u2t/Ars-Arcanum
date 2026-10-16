"""Native Zero-Pip EPUB3 Package Builder for Ars Arcanum.

Generates standard-compliant, air-gapped EPUB3 digital books using strictly
the Python >= 3.10 standard library (zipfile, xml.etree, html).
Eliminates external binary requirements (Pandoc) for sovereign eBook publication.
"""

from __future__ import annotations

import html
import logging
import os
import re
import sys
import time
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.arcanum.publishing.publisher import resolve_prose_for_publication

logger = logging.getLogger("arcanum.publishing.epub")

_ILLEGAL_XML_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")
_THEMATIC_BREAK_RE = re.compile(r"^\s*(?:(?:\*\s*){3,}|(?:-\s*){3,}|(?:_\s*){3,})\s*$")
_BLOCKQUOTE_RE = re.compile(r"^>\s*(.+)$")
_DIRECTIVE_RE = re.compile(r"^\s*@[A-Za-z0-9_-]+:.*$", re.MULTILINE)

DEFAULT_CSS: str = """@charset "UTF-8";
body {
  font-family: Georgia, "Times New Roman", serif;
  font-size: 1.05em;
  line-height: 1.6;
  margin: 5%;
  color: #1a1a1a;
  background-color: #ffffff;
}
h1, h2, h3, h4 {
  font-family: Georgia, "Times New Roman", serif;
  text-align: center;
  font-weight: normal;
  margin-top: 2.5em;
  margin-bottom: 1.2em;
  page-break-after: avoid;
}
h1 { font-size: 1.8em; }
h2 { font-size: 1.4em; }
h3 { font-size: 1.2em; }
p {
  text-indent: 1.5em;
  margin-top: 0;
  margin-bottom: 0;
  text-align: justify;
}
p.first-p, section > p:first-of-type, hr + p {
  text-indent: 0;
}
hr.thematic-break {
  border: none;
  text-align: center;
  margin: 2em 0;
}
hr.thematic-break::after {
  content: "* * *";
  font-size: 1.1em;
  letter-spacing: 0.4em;
  color: #666666;
}
blockquote {
  margin: 1.5em 2em;
  font-style: italic;
  color: #333333;
}
nav#toc ol {
  list-style-type: none;
  padding-left: 0;
}
nav#toc li {
  margin: 0.75em 0;
}
nav#toc a {
  text-decoration: none;
  color: #2b4c7e;
}
.cover-container {
  text-align: center;
  margin: 0;
  padding: 0;
}
.cover-container img {
  max-width: 100%;
  max-height: 100%;
  height: auto;
}
"""


def clean_xml_text(text: str) -> str:
    """Strip illegal XML 1.0 control characters."""
    return _ILLEGAL_XML_CHARS.sub("", text)


def inline_markdown_to_xhtml(text: str) -> str:
    """Converts inline markdown formatting (bold, italic, code, strikethrough) to valid XHTML."""
    clean = clean_xml_text(text)
    escaped = html.escape(clean, quote=True)

    # Bold & Italic (*** or ___)
    escaped = re.sub(r"\*\*\*([^*]+)\*\*\*", r"<strong><em>\1</em></strong>", escaped)
    escaped = re.sub(r"___([^_]+)___", r"<strong><em>\1</em></strong>", escaped)
    # Bold (** or __)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"__([^_]+)__", r"<strong>\1</strong>", escaped)
    # Italic (* or _)
    escaped = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", escaped)
    escaped = re.sub(r"(?<!\w)_([^_]+)_(?!\w)", r"<em>\1</em>", escaped)
    # Strikethrough (~~)
    escaped = re.sub(r"~~([^~]+)~~", r"<del>\1</del>", escaped)
    # Code (`)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    # Line breaks inside paragraph
    return escaped.replace("\n", "<br />\n")


def markdown_to_xhtml_body(body_md: str) -> str:
    """Parses chapter Markdown into well-formed XHTML5 section body."""
    resolved = resolve_prose_for_publication(body_md)
    cleaned = _DIRECTIVE_RE.sub("", resolved)

    paragraphs = re.split(r"\r?\n\s*\r?\n", cleaned.strip())
    xhtml_elements: list[str] = []

    for para in paragraphs:
        raw_p = para.strip()
        if not raw_p:
            continue

        # Thematic break (* * *, ---, ___)
        if _THEMATIC_BREAK_RE.match(raw_p):
            xhtml_elements.append('    <hr class="thematic-break" />')
            continue

        # Heading (# Chapter)
        heading_match = _HEADING_RE.match(raw_p)
        if heading_match:
            level = min(6, len(heading_match.group(1)) + 1)
            htext = inline_markdown_to_xhtml(heading_match.group(2).strip())
            xhtml_elements.append(f"    <h{level}>{htext}</h{level}>")
            continue

        # Blockquote (> Quote)
        bq_match = _BLOCKQUOTE_RE.match(raw_p)
        if bq_match:
            bq_lines = [line.lstrip("> ").strip() for line in raw_p.splitlines()]
            bq_text = inline_markdown_to_xhtml(" ".join(bq_lines))
            xhtml_elements.append(f"    <blockquote><p>{bq_text}</p></blockquote>")
            continue

        # Standard prose paragraph
        p_text = inline_markdown_to_xhtml(raw_p)
        xhtml_elements.append(f"    <p>{p_text}</p>")

    return "\n".join(xhtml_elements)


def build_native_epub3(
    output_path: Path | str,
    chapters: list[dict[str, Any]],
    meta: dict[str, Any],
    cover_path: Path | str | None = None,
) -> dict[str, Any]:
    """Compiles a list of manuscript chapters into an air-gapped, standard-compliant EPUB3 file.

    Zero third-party pip dependencies; uses Python standard library zipfile.
    """
    out = Path(output_path).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    title = html.escape(str(meta.get("title", out.stem)), quote=True)
    author = html.escape(str(meta.get("author", "Author")), quote=True)
    language = html.escape(str(meta.get("language", "en")), quote=True)
    book_id = str(meta.get("identifier") or uuid.uuid4())
    mod_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    zip_dt = time.localtime(time.time())[:6]

    # Verify cover image if provided
    cover_file: Path | None = None
    cover_media_type = "image/jpeg"
    if cover_path:
        cp = Path(cover_path).resolve()
        if cp.is_file():
            cover_file = cp
            cover_media_type = "image/png" if cp.suffix.lower() == ".png" else "image/jpeg"

    # Stage temporary zip file with atomic replacement
    tmp_epub = out.with_suffix(".epub.tmp")
    try:
        with zipfile.ZipFile(tmp_epub, "w") as zf:
            # 1. mimetype MUST be the very first entry, uncompressed (ZIP_STORED)
            mimetype_info = zipfile.ZipInfo("mimetype", date_time=zip_dt)
            mimetype_info.compress_type = zipfile.ZIP_STORED
            zf.writestr(mimetype_info, b"application/epub+zip")

            # 2. META-INF/container.xml
            container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""
            zf.writestr(
                zipfile.ZipInfo("META-INF/container.xml", date_time=zip_dt),
                container_xml.encode("utf-8"),
                compress_type=zipfile.ZIP_DEFLATED,
            )

            # 3. OEBPS/style.css
            zf.writestr(
                zipfile.ZipInfo("OEBPS/style.css", date_time=zip_dt),
                DEFAULT_CSS.encode("utf-8"),
                compress_type=zipfile.ZIP_DEFLATED,
            )

            # 4. Cover image if exists
            if cover_file:
                cover_ext = cover_file.suffix.lower()
                cover_dest = f"OEBPS/cover{cover_ext}"
                zf.writestr(
                    zipfile.ZipInfo(cover_dest, date_time=zip_dt),
                    cover_file.read_bytes(),
                    compress_type=zipfile.ZIP_DEFLATED,
                )
                cover_xhtml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="{language}" lang="{language}">
<head>
  <meta charset="UTF-8" />
  <title>Cover</title>
  <link rel="stylesheet" type="text/css" href="style.css" />
</head>
<body>
  <div class="cover-container" epub:type="cover">
    <img src="cover{cover_ext}" alt="Cover" />
  </div>
</body>
</html>"""
                zf.writestr(
                    zipfile.ZipInfo("OEBPS/cover.xhtml", date_time=zip_dt),
                    cover_xhtml.encode("utf-8"),
                    compress_type=zipfile.ZIP_DEFLATED,
                )

            # 5. Chapter XHTML documents
            manifest_items: list[str] = [
                '    <item id="style" href="style.css" media-type="text/css" />',
                '    <item id="toc" href="toc.xhtml" media-type="application/xhtml+xml" properties="nav" />',
            ]
            spine_refs: list[str] = []
            toc_links: list[str] = []

            if cover_file:
                cover_ext = cover_file.suffix.lower()
                manifest_items.append(f'    <item id="cover-image" href="cover{cover_ext}" media-type="{cover_media_type}" properties="cover-image" />')
                manifest_items.append('    <item id="cover-page" href="cover.xhtml" media-type="application/xhtml+xml" />')
                spine_refs.append('    <itemref idref="cover-page" />')

            for idx, ch in enumerate(chapters, 1):
                ch_id = f"chapter_{idx:03d}"
                ch_filename = f"{ch_id}.xhtml"
                ch_title = html.escape(str(ch.get("title", f"Chapter {idx}")), quote=True)
                body_content = markdown_to_xhtml_body(str(ch.get("body", "")))

                ch_xhtml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="{language}" lang="{language}">
<head>
  <meta charset="UTF-8" />
  <title>{ch_title}</title>
  <link rel="stylesheet" type="text/css" href="style.css" />
</head>
<body>
  <section epub:type="chapter">
    <h2>{ch_title}</h2>
{body_content}
  </section>
</body>
</html>"""
                zf.writestr(
                    zipfile.ZipInfo(f"OEBPS/{ch_filename}", date_time=zip_dt),
                    ch_xhtml.encode("utf-8"),
                    compress_type=zipfile.ZIP_DEFLATED,
                )
                manifest_items.append(f'    <item id="{ch_id}" href="{ch_filename}" media-type="application/xhtml+xml" />')
                spine_refs.append(f'    <itemref idref="{ch_id}" />')
                toc_links.append(f'      <li><a href="{ch_filename}">{ch_title}</a></li>')

            # 6. OEBPS/toc.xhtml (Nav document)
            toc_xhtml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="{language}" lang="{language}">
<head>
  <meta charset="UTF-8" />
  <title>Table of Contents</title>
  <link rel="stylesheet" type="text/css" href="style.css" />
</head>
<body>
  <nav epub:type="toc" id="toc">
    <h1>Table of Contents</h1>
    <ol>
{chr(10).join(toc_links)}
    </ol>
  </nav>
</body>
</html>"""
            zf.writestr(
                zipfile.ZipInfo("OEBPS/toc.xhtml", date_time=zip_dt),
                toc_xhtml.encode("utf-8"),
                compress_type=zipfile.ZIP_DEFLATED,
            )

            # 7. OEBPS/content.opf (Package document)
            content_opf = f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="pub-id">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="pub-id">urn:uuid:{book_id}</dc:identifier>
    <dc:title>{title}</dc:title>
    <dc:creator>{author}</dc:creator>
    <dc:language>{language}</dc:language>
    <meta property="dcterms:modified">{mod_time}</meta>
  </metadata>
  <manifest>
{chr(10).join(manifest_items)}
  </manifest>
  <spine>
{chr(10).join(spine_refs)}
  </spine>
</package>"""
            zf.writestr(
                zipfile.ZipInfo("OEBPS/content.opf", date_time=zip_dt),
                content_opf.encode("utf-8"),
                compress_type=zipfile.ZIP_DEFLATED,
            )

        # Atomic file promotion with Windows retry backoff
        for attempt in range(5):
            try:
                os.replace(tmp_epub, out)
                break
            except PermissionError:
                if attempt == 4 or sys.platform != "win32":
                    raise
                time.sleep(0.02 * (2**attempt))

    except Exception:
        if tmp_epub.exists():
            try:
                tmp_epub.unlink()
            except OSError:
                pass
        raise

    return {
        "status": "success",
        "format": "epub",
        "builder": "native_zero_pip_epub3",
        "output_path": str(out),
        "size_bytes": out.stat().st_size if out.exists() else 0,
        "chapters_count": len(chapters),
    }
