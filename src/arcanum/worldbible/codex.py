"""Ars Arcanum Static World Wiki & Lore Codex Exporter.

Module: src/arcanum/worldbible/codex.py
Compiles Obsidian World Bibles into a sovereign, searchable, single-file offline encyclopedia.

Engineering Contracts:
- 100% sovereign offline architecture (zero cloud telemetry, zero external CDN dependencies).
- Strict Content-Security-Policy: default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:; media-src data: blob:;
- Strict path traversal defense with `is_safe_subpath`.
- Atomic writes with Windows backoff retry (`atomic_write`).
"""

from __future__ import annotations

import argparse
import html
import json
import logging
import re
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from src.arcanum.core.storage import PathSecurityError, atomic_write, is_safe_subpath

logger = logging.getLogger("arcanum.worldbible.codex")

TAXONOMIES: list[str] = [
    "Characters",
    "Locations",
    "Factions",
    "Artifacts",
    "Bestiary",
    "Cosmology",
    "Languages",
    "MagicSystems",
    "History",
]

_FRONTMATTER_BOUNDARY_RE = re.compile(r"\A---\s*\r?\n(.*?)\r?\n---\s*(?:\r?\n|\Z)", re.DOTALL)


def parse_frontmatter(markdown_text: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter header and return (frontmatter_dict, markdown_body)."""
    match = _FRONTMATTER_BOUNDARY_RE.match(markdown_text)
    if not match:
        return {}, markdown_text

    raw_yaml = match.group(1)
    body = markdown_text[match.end() :]
    metadata: dict[str, Any] = {}
    for line in raw_yaml.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key_part, val_part = line.split(":", 1)
        key = key_part.strip()
        val_str = val_part.strip()
        if val_str and not val_str.startswith(('"', "'")):
            val_str = re.sub(r"\s+#.*$", "", val_str).strip()
        metadata[key] = val_str.strip("'\"")
    return metadata, body


def convert_markdown_to_styled_html(raw_body: str) -> str:
    """Convert raw Markdown body to clean HTML with Obsidian wikilinks and basic styling."""
    escaped_body = html.escape(raw_body)

    # Convert wikilinks: [[Target|Label]] -> <a href="#Target" class="wikilink">Label</a>
    def _sub_wikilink(m: re.Match[str]) -> str:
        target = m.group(1).strip()
        label = m.group(2).strip() if m.group(2) else target
        clean_target = html.unescape(target).replace(" ", "_")
        clean_id = re.sub(r"[^\w\-]", "", clean_target)
        return f'<a href="#{clean_id}" class="wikilink">{label}</a>'

    body_html = re.sub(r"\[\[([^\|\]]+)(?:\|([^\]]+))?\]\]", _sub_wikilink, escaped_body)

    # Headings
    body_html = re.sub(r"^###\s+(.*)$", r"<h3>\1</h3>", body_html, flags=re.MULTILINE)
    body_html = re.sub(r"^##\s+(.*)$", r"<h2>\1</h2>", body_html, flags=re.MULTILINE)
    body_html = re.sub(r"^#\s+(.*)$", r"<h1>\1</h1>", body_html, flags=re.MULTILINE)

    # Bold and italics
    body_html = re.sub(r"\*\*\*(.*?)\*\*\*", r"<strong><em>\1</em></strong>", body_html)
    body_html = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", body_html)
    body_html = re.sub(r"\*(.*?)\*", r"<em>\1</em>", body_html)

    # Paragraphs
    paragraphs = body_html.split("\n\n")
    p_tags: list[str] = []
    for p in paragraphs:
        p_clean = p.strip()
        if not p_clean:
            continue
        if p_clean.startswith("<h"):
            p_tags.append(p_clean)
        else:
            p_tags.append(f"<p>{p_clean.replace(chr(10), '<br>')}</p>")

    return "\n".join(p_tags)


def convert_markdown_to_basic_html(md_text: str) -> tuple[str, dict[str, Any]]:
    """Convert Markdown text to clean HTML and return (html_body, frontmatter_dict)."""
    fm, body = parse_frontmatter(md_text)
    return convert_markdown_to_styled_html(body), fm


def scan_world_vault(
    world_dir: Path,
    taxonomies: Sequence[str] | None = None,
    *,
    scope: Any = None,
) -> dict[str, list[dict[str, Any]]]:
    """Scan world vault notes grouped by taxonomy directories."""
    resolved_world = world_dir.resolve()
    categories: dict[str, list[dict[str, Any]]] = {}

    target_taxonomies = list(taxonomies) if taxonomies is not None else TAXONOMIES
    if scope and getattr(scope, "lore_categories", None):
        cat_lowers = {c.lower() for c in scope.lore_categories}
        target_taxonomies = [t for t in target_taxonomies if t.lower() in cat_lowers]

    for tax in target_taxonomies:
        tax_dir = resolved_world / tax
        if not tax_dir.is_dir():
            continue
        if not is_safe_subpath(resolved_world, tax_dir):
            raise PathSecurityError(f"Taxonomy directory escapes world root: {tax_dir}")

        items: list[dict[str, Any]] = []
        for f in sorted(tax_dir.glob("*.md")):
            if f.name.startswith("."):
                continue
            raw_text = f.read_text(encoding="utf-8")
            fm, body = parse_frontmatter(raw_text)
            title = fm.get("name") or fm.get("title") or f.stem.replace("_", " ")
            clean_id = re.sub(r"[^a-zA-Z0-9_\-]", "", f.stem)
            body_html = convert_markdown_to_styled_html(body)
            items.append({
                "id": clean_id,
                "clean_id": clean_id,
                "title": str(title),
                "taxonomy": tax,
                "tax": tax,
                "filename": f.name,
                "frontmatter": fm,
                "html": body_html,
                "html_content": body_html,
                "body_html": body_html,
                "raw_body": body,
                "raw_text": body[:300],
            })
        if items:
            categories[tax] = items

    return categories


def render_codex_html(
    categories: dict[str, list[dict[str, Any]]],
    world_name: str,
    output_path: Path | str | None = None,
) -> Path | str:
    """Render a self-contained offline interactive World Wiki Codex."""
    total_articles = sum(len(items) for items in categories.values())

    sidebar_links: list[str] = []
    entries_html: list[str] = []
    search_index: list[dict[str, str]] = []

    for tax, items in sorted(categories.items()):
        if not items:
            continue
        sidebar_links.append(f'<div class="tax-header">{html.escape(tax)} ({len(items)})</div>')
        for item in sorted(items, key=lambda x: str(x["title"])):
            clean_id = str(item["clean_id"])
            title = str(item["title"])
            sidebar_links.append(
                f'<a href="#{clean_id}" class="nav-link" onclick="showArticle(\'{clean_id}\')">{html.escape(title)}</a>'
            )

            # Build infobox rows
            infobox_rows: list[str] = []
            fm = item.get("frontmatter", {})
            if isinstance(fm, dict):
                for k, v in sorted(fm.items()):
                    if k not in ("title", "type", "tax") and str(v).strip():
                        infobox_rows.append(
                            f"<tr><th>{html.escape(str(k).title())}</th><td>{html.escape(str(v))}</td></tr>"
                        )

            infobox_html = ""
            if infobox_rows:
                infobox_html = f"""
                <table class="infobox">
                  <thead><tr><th colspan="2" class="infobox-title">{html.escape(title)}</th></tr></thead>
                  <tbody>{''.join(infobox_rows)}</tbody>
                </table>
                """

            article_body = str(item.get("html_content") or item.get("body_html") or item.get("html") or "")
            entries_html.append(f"""
            <article id="{clean_id}" class="codex-article" style="display:none;">
              <div class="article-header">
                <span class="tax-badge">{html.escape(tax)}</span>
                <h1>{html.escape(title)}</h1>
              </div>
              {infobox_html}
              <div class="article-body">
                {article_body}
              </div>
            </article>
            """)

            search_index.append({
                "id": clean_id,
                "title": title,
                "tax": tax,
                "text": str(item.get("raw_body", ""))[:300],
            })

    search_json = json.dumps(search_index).replace("</", "<\\/")

    html_content = f"""<!DOCTYPE html>
<html lang="en" data-theme="sovereign-dark">
<head>
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:; media-src data: blob:;">
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Ars Arcanum — {html.escape(world_name)} Codex</title>
<style>
  :root {{
    --bg: #0f172a; --panel: #1e293b; --border: #334155;
    --text: #f8fafc; --muted: #94a3b8; --accent: #38bdf8;
    --link: #60a5fa; --infobox-bg: #1e293b;
  }}
  body[data-theme="light"] {{
    --bg: #f8fafc; --panel: #ffffff; --border: #cbd5e1;
    --text: #0f172a; --muted: #64748b; --accent: #0284c7;
    --link: #2563eb; --infobox-bg: #f1f5f9;
  }}
  body[data-theme="sepia"] {{
    --bg: #f4ecd8; --panel: #faf4e6; --border: #dcd0ba;
    --text: #3c2f1e; --muted: #7c6f5a; --accent: #b45309;
    --link: #92400e; --infobox-bg: #eee5d0;
  }}
  body {{ font-family: system-ui, -apple-system, sans-serif; background: var(--bg); color: var(--text); margin: 0; display: flex; height: 100vh; overflow: hidden; }}
  #sidebar {{ width: 320px; background: var(--panel); border-right: 1px solid var(--border); display: flex; flex-direction: column; }}
  .sidebar-header {{ padding: 1.25rem; border-bottom: 1px solid var(--border); }}
  .sidebar-header h2 {{ margin: 0; color: var(--accent); font-size: 1.25rem; }}
  .search-input {{ width: 100%; box-sizing: border-box; padding: 0.6rem; margin-top: 0.75rem; background: var(--bg); border: 1px solid var(--border); border-radius: 6px; color: var(--text); }}
  .nav-container {{ overflow-y: auto; flex: 1; padding: 0.75rem; }}
  .tax-header {{ font-size: 0.75rem; text-transform: uppercase; color: var(--muted); font-weight: 700; margin: 1rem 0 0.25rem 0.5rem; }}
  .nav-link {{ display: block; padding: 0.4rem 0.5rem; color: var(--text); text-decoration: none; border-radius: 4px; font-size: 0.875rem; }}
  .nav-link:hover, .nav-link.active {{ background: var(--bg); color: var(--accent); }}
  #main {{ flex: 1; overflow-y: auto; padding: 2.5rem; }}
  .theme-toggle {{ position: fixed; top: 1rem; right: 1.5rem; display: flex; gap: 0.5rem; z-index: 10; }}
  .btn-theme {{ background: var(--panel); border: 1px solid var(--border); color: var(--text); padding: 0.4rem 0.75rem; border-radius: 6px; cursor: pointer; font-size: 0.8rem; }}
  .tax-badge {{ background: #334155; color: var(--accent); padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; }}
  .infobox {{ float: right; margin: 0 0 1.5rem 1.5rem; background: var(--infobox-bg); border: 1px solid var(--border); border-radius: 8px; width: 280px; border-collapse: collapse; font-size: 0.85rem; }}
  .infobox-title {{ background: var(--border); padding: 0.5rem; font-size: 1rem; text-align: center; color: var(--accent); }}
  .infobox th, .infobox td {{ padding: 0.4rem 0.6rem; text-align: left; border-bottom: 1px solid var(--border); }}
  .wikilink {{ color: var(--link); text-decoration: underline; }}
  .home-splash {{ max-width: 700px; margin: 3rem auto; text-align: center; }}
</style>
</head>
<body>

<div id="sidebar">
  <div class="sidebar-header">
    <h2>📖 {html.escape(world_name)} Codex</h2>
    <p style="color:var(--muted); font-size:0.8rem; margin:4px 0 0 0;">{total_articles} Articles Indexed</p>
    <input type="text" id="search" class="search-input" placeholder="Search world lore..." oninput="doSearch()">
  </div>
  <div class="nav-container" id="navLinks">
    {''.join(sidebar_links)}
  </div>
</div>

<main id="main">
  <div class="theme-toggle">
    <button class="btn-theme" onclick="setTheme('dark')">Dark</button>
    <button class="btn-theme" onclick="setTheme('light')">Light</button>
    <button class="btn-theme" onclick="setTheme('sepia')">Sepia</button>
  </div>

  <div id="homeView" class="home-splash">
    <h1 style="color:var(--accent); font-size:2.5rem; margin-bottom:0.5rem;">{html.escape(world_name)}</h1>
    <p style="color:var(--muted); font-size:1.1rem;">A sovereign, static encyclopedia of lore, history, factions, and characters.</p>
    <p style="color:var(--muted);">Select an entry from the sidebar navigation or use search to explore.</p>
  </div>

  {''.join(entries_html)}
</main>

<script>
function escapeHtml(str) {{
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}}

const index = {search_json};
let originalNavHtml = '';

function setTheme(name) {{
  document.body.setAttribute('data-theme', name);
}}

function showArticle(id) {{
  document.getElementById('homeView').style.display = 'none';
  document.querySelectorAll('.codex-article').forEach(a => a.style.display = 'none');
  const target = document.getElementById(id);
  if (target) {{
    target.style.display = 'block';
    if (window.location.hash.replace('#', '') !== id) {{
      window.location.hash = id;
    }}
  }}
}}

function doSearch() {{
  const q = document.getElementById('search').value.toLowerCase().trim();
  const nav = document.getElementById('navLinks');
  if (!originalNavHtml) originalNavHtml = nav.innerHTML;
  if (!q) {{
    nav.innerHTML = originalNavHtml;
    return;
  }}
  const matches = index.filter(item => item.title.toLowerCase().includes(q) || item.text.toLowerCase().includes(q));
  nav.innerHTML = '<div class="tax-header">Search Results (' + matches.length + ')</div>';
  matches.forEach(m => {{
    const a = document.createElement('a');
    a.className = 'nav-link';
    a.href = '#' + encodeURIComponent(m.id);
    a.innerHTML = `<strong>${{escapeHtml(m.title)}}</strong> <small style="color:var(--muted);">(${{escapeHtml(m.tax)}})</small>`;
    a.onclick = () => showArticle(m.id);
    nav.appendChild(a);
  }});
}}

function handleHash() {{
  const hash = window.location.hash.replace('#', '');
  if (hash) showArticle(hash);
}}

window.addEventListener('load', () => {{
  originalNavHtml = document.getElementById('navLinks').innerHTML;
  handleHash();
}});
window.addEventListener('hashchange', handleHash);
</script>
</body>
</html>
"""
    if output_path is not None:
        target = Path(output_path).resolve()
        atomic_write(target, html_content)
        return target
    return html_content


def build_single_file_codex(
    categories: dict[str, list[dict[str, Any]]],
    world_name: str,
    output_path: Path,
) -> Path:
    """Build a single standalone offline HTML file containing the complete world codex."""
    res = render_codex_html(categories, world_name=world_name, output_path=output_path)
    return Path(res)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for `arcanum codex-export`."""
    parser = argparse.ArgumentParser(description="Ars Arcanum Static World Wiki Codex Exporter (WOR-102)")
    parser.add_argument("world", nargs="?", help="World Lore Vault directory path")
    parser.add_argument("-o", "--output", help="Output file path (default: <world_name>_codex.html)")
    parser.add_argument("--html", help="Generate HTML codex export at path")
    parser.add_argument("--open", action="store_true", help="Open generated codex in default browser")
    parser.add_argument("--json", action="store_true", help="Output JSON vault taxonomy index")
    args = parser.parse_args(argv)

    raw_world = args.world or "."
    world_path = Path(raw_world).resolve()
    if not world_path.is_dir():
        sys.stderr.write(f"Error: World directory not found: {world_path}\n")
        return 1

    categories = scan_world_vault(world_path)

    if args.json:
        sys.stdout.write(json.dumps({tax: len(items) for tax, items in categories.items()}, indent=2) + "\n")
        return 0

    out_file = Path(args.html or args.output or f"{world_path.name}_codex.html")
    build_single_file_codex(categories, world_name=world_path.name, output_path=out_file)

    total_articles = sum(len(items) for items in categories.values())
    sys.stdout.write("=== Ars Arcanum Static Codex Exporter ===\n")
    sys.stdout.write(f"World:          {world_path.name}\n")
    sys.stdout.write(f"Total Articles: {total_articles} across {len(categories)} categories\n")
    sys.stdout.write(f"Generated:      {out_file} ({out_file.stat().st_size:,} bytes)\n")
    if getattr(args, "open", False):
        import webbrowser
        try:
            webbrowser.open(out_file.resolve().as_uri())
        except Exception as exc:
            sys.stderr.write(f"Warning: Could not open browser: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
