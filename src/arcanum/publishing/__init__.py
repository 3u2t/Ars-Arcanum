"""Publishing, OpenXML Tracked Changes, EPUB3, and typesetting compilers."""

from __future__ import annotations

from scripts.lib.audit_hardening import (
    export_markdown_to_docx_hardened,
    pull_docx_to_markdown_hardened,
)
from src.arcanum.publishing.docx import (
    build_tracked_document_xml,
    export_markdown_to_docx,
    pull_docx_to_markdown,
)
from src.arcanum.publishing.epub import (
    build_native_epub3,
)
from src.arcanum.publishing.omnibus import (
    VolumeData,
    compile_omnibus_manuscript,
    discover_series_volumes,
    generate_omnibus_html_reader,
)
from src.arcanum.publishing.preflight import (
    check_cover_and_assets,
    check_metadata,
    generate_preflight_html_report,
    run_preflight_linter,
    validate_chapter_formatting,
)
from src.arcanum.publishing.publisher import (
    collect_manuscript_content,
    compile_docx,
    compile_pandoc_epub,
    compile_typst_pdf,
    escape_typst_text,
    get_manuscript_metadata,
    publish_manuscript,
    resolve_prose_for_publication,
)

__all__ = [
    "VolumeData",
    "build_native_epub3",
    "build_tracked_document_xml",
    "check_cover_and_assets",
    "check_metadata",
    "collect_manuscript_content",
    "compile_docx",
    "compile_omnibus_manuscript",
    "compile_pandoc_epub",
    "compile_typst_pdf",
    "discover_series_volumes",
    "escape_typst_text",
    "export_markdown_to_docx",
    "export_markdown_to_docx_hardened",
    "generate_omnibus_html_reader",
    "generate_preflight_html_report",
    "get_manuscript_metadata",
    "publish_manuscript",
    "pull_docx_to_markdown",
    "pull_docx_to_markdown_hardened",
    "resolve_prose_for_publication",
    "run_preflight_linter",
    "validate_chapter_formatting",
]
