"""Ars Arcanum Standalone HTML & SVG Visualizer Generators (src/arcanum/worldbible/visualizers.py).

Provides offline, air-gapped, interactive standalone HTML viewers for:
1. Planetary Orbital Calendar Wheels
2. PolyGlot Conlang Etymology Trees
3. Multi-POV Narrative Braids

All exported HTML files enforce strict Content Security Policy (default-src 'none'),
support dark/light/sepia sovereign themes, client-side SVG download, and interactive zoom/pan.
"""

from __future__ import annotations

import html
from pathlib import Path

from src.arcanum.worldbible.conlang import ConlangLexeme, render_etymology_tree_svg
from src.arcanum.worldbible.timeline import CustomCalendarSpec, render_orbital_calendar_svg
from src.arcanum.core.storage import atomic_write


def wrap_svg_in_standalone_html(
    svg_content: str,
    title: str,
    subtitle: str = "",
    metadata_cards: list[dict[str, str]] | None = None,
    default_theme: str = "dark",
) -> str:
    """Wraps an SVG diagram inside a self-contained, air-gapped interactive HTML visualizer."""
    safe_title = html.escape(title)
    safe_subtitle = html.escape(subtitle)
    cards = metadata_cards or []

    cards_html = "".join(
        f"""
        <div class="kpi-card">
          <div class="kpi-val">{html.escape(str(c.get('value', '')))}</div>
          <div class="kpi-lbl">{html.escape(str(c.get('label', '')))}</div>
        </div>
        """
        for c in cards
    )

    return f"""<!DOCTYPE html>
<html lang="en" data-theme="{html.escape(default_theme)}">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:; connect-src 'none';">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Ars Arcanum — {safe_title}</title>
  <style>
    :root {{
      --bg: #0b0f19;
      --surface: #111827;
      --surface-elevated: #1a2234;
      --surface-hover: #222e44;
      --border: #233148;
      --text: #f1f5f9;
      --text-muted: #94a3b8;
      --accent: #38bdf8;
      --font-sans: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }}
    html[data-theme="light"] {{
      --bg: #f8fafc;
      --surface: #ffffff;
      --surface-elevated: #f1f5f9;
      --surface-hover: #e2e8f0;
      --border: #cbd5e1;
      --text: #0f172a;
      --text-muted: #64748b;
      --accent: #0284c7;
    }}
    html[data-theme="sepia"] {{
      --bg: #f4ecd8;
      --surface: #faf4e6;
      --surface-elevated: #eee5d0;
      --surface-hover: #e4d8be;
      --border: #dcd0ba;
      --text: #3c2f1e;
      --text-muted: #7c6f5a;
      --accent: #b45309;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: var(--font-sans);
      background: var(--bg);
      color: var(--text);
      display: flex;
      flex-direction: column;
      min-height: 100vh;
      overflow-x: hidden;
    }}
    header {{
      background: var(--surface);
      border-bottom: 1px solid var(--border);
      padding: 1rem 2rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 1rem;
    }}
    .brand {{
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }}
    .brand h1 {{
      font-size: 1.25rem;
      font-weight: 700;
      letter-spacing: -0.01em;
      color: var(--accent);
    }}
    .brand .subtitle {{
      font-size: 0.85rem;
      color: var(--text-muted);
    }}
    .toolbar {{
      display: flex;
      align-items: center;
      gap: 0.5rem;
      flex-wrap: wrap;
    }}
    button, .btn {{
      background: var(--surface-elevated);
      color: var(--text);
      border: 1px solid var(--border);
      padding: 0.4rem 0.8rem;
      border-radius: 6px;
      font-size: 0.82rem;
      font-weight: 500;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      transition: all 0.15s ease;
    }}
    button:hover, .btn:hover {{
      background: var(--surface-hover);
      border-color: var(--accent);
      color: var(--accent);
    }}
    .btn-primary {{
      background: var(--accent);
      color: #0b0f19;
      border-color: var(--accent);
      font-weight: 600;
    }}
    .btn-primary:hover {{
      background: #7dd3fc;
      color: #0b0f19;
    }}
    .kpi-strip {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
      gap: 0.75rem;
      padding: 1rem 2rem;
      background: var(--surface);
      border-bottom: 1px solid var(--border);
    }}
    .kpi-card {{
      background: var(--surface-elevated);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 0.6rem 0.85rem;
    }}
    .kpi-val {{
      font-size: 1.2rem;
      font-weight: 700;
      color: var(--accent);
      font-family: var(--font-mono);
    }}
    .kpi-lbl {{
      font-size: 0.72rem;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    main {{
      flex: 1;
      display: flex;
      justify-content: center;
      align-items: center;
      padding: 1.5rem;
      overflow: auto;
      background: var(--bg);
    }}
    #viewport-container {{
      max-width: 100%;
      max-height: 85vh;
      overflow: auto;
      display: flex;
      justify-content: center;
      align-items: center;
      border: 1px solid var(--border);
      border-radius: 8px;
      background: var(--surface);
      padding: 1.5rem;
      box-shadow: 0 4px 20px rgba(0,0,0,0.25);
    }}
    #svg-viewport {{
      transform-origin: center center;
      transition: transform 0.15s ease;
      display: flex;
      justify-content: center;
      align-items: center;
    }}
    footer {{
      padding: 0.75rem 2rem;
      background: var(--surface);
      border-top: 1px solid var(--border);
      font-size: 0.75rem;
      color: var(--text-muted);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <span style="font-size: 1.4rem;">🏛️</span>
      <div>
        <h1>{safe_title}</h1>
        <div class="subtitle">{safe_subtitle or "Sovereign 100% Offline Visualizer"}</div>
      </div>
    </div>
    <div class="toolbar">
      <span id="zoom-level" style="font-size:0.8rem; font-family:var(--font-mono); color:var(--text-muted); padding:0 0.4rem;">100%</span>
      <button onclick="adjustZoom(0.1)" title="Zoom In">🔍 +</button>
      <button onclick="adjustZoom(-0.1)" title="Zoom Out">🔍 −</button>
      <button onclick="resetZoom()" title="Reset Zoom">↺</button>
      <button onclick="setTheme('dark')" title="Dark Theme">🌙 Dark</button>
      <button onclick="setTheme('light')" title="Light Theme">☀️ Light</button>
      <button onclick="setTheme('sepia')" title="Sepia Theme">📜 Sepia</button>
      <button class="btn btn-primary" onclick="exportSvg()" title="Download SVG File">💾 Download SVG</button>
    </div>
  </header>

  {f'<div class="kpi-strip">{cards_html}</div>' if cards else ''}

  <main>
    <div id="viewport-container">
      <div id="svg-viewport">
        {svg_content}
      </div>
    </div>
  </main>

  <footer>
    <span>Ars Arcanum (Scriptorium) — Sovereign Worldbuilding Architecture</span>
    <span>100% Offline · Zero Telemetry · CSP Air-Gapped</span>
  </footer>

  <script>
    let currentZoom = 1.0;

    function adjustZoom(delta) {{
      currentZoom = Math.max(0.3, Math.min(3.0, currentZoom + delta));
      applyZoom();
    }}

    function resetZoom() {{
      currentZoom = 1.0;
      applyZoom();
    }}

    function applyZoom() {{
      const vp = document.getElementById('svg-viewport');
      if (vp) {{
        vp.style.transform = `scale(${{currentZoom.toFixed(2)}})`;
      }}
      const lbl = document.getElementById('zoom-level');
      if (lbl) {{
        lbl.textContent = `${{Math.round(currentZoom * 100)}}%`;
      }}
    }}

    function setTheme(theme) {{
      document.documentElement.setAttribute('data-theme', theme);
    }}

    function exportSvg() {{
      const vp = document.getElementById('svg-viewport');
      if (!vp) return;
      const svg = vp.querySelector('svg');
      if (!svg) return;
      const content = new XMLSerializer().serializeToString(svg);
      const uri = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(content);
      const a = document.createElement('a');
      a.href = uri;
      a.download = '{Path(title.lower().replace(" ", "_")).stem}.svg';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }}
  </script>
</body>
</html>
"""


def export_orbital_calendar_html(
    spec: CustomCalendarSpec,
    output_path: Path | str,
    theme: str = "dark",
    width: int = 700,
    height: int = 700,
) -> Path:
    """Renders and saves a standalone interactive HTML planetary calendar visualizer."""
    out_path = Path(output_path).resolve()
    svg = render_orbital_calendar_svg(spec, width=width, height=height, theme=theme)

    month_min = min(spec.month_lengths) if spec.month_lengths else 0
    month_max = max(spec.month_lengths) if spec.month_lengths else 0
    month_range = f"{month_min}d" if month_min == month_max else f"{month_min}–{month_max}d"
    cards = [
        {"label": "Days Per Year", "value": f"{spec.days_per_year:,}"},
        {"label": "Months", "value": f"{len(spec.month_lengths)}"},
        {"label": "Calendar Name", "value": spec.calendar_name},
        {"label": "Month Lengths", "value": month_range},
    ]

    html_doc = wrap_svg_in_standalone_html(
        svg_content=svg,
        title=f"{spec.calendar_name} — Orbital Calendar",
        subtitle=f"{len(spec.month_lengths)} Months · {spec.days_per_year} Days per Orbital Revolution",
        metadata_cards=cards,
        default_theme=theme,
    )
    atomic_write(out_path, html_doc)
    return out_path


def export_etymology_tree_html(
    lexemes: list[ConlangLexeme],
    output_path: Path | str,
    theme: str = "dark",
    width: int = 900,
    height: int = 550,
    title: str = "PolyGlot Conlang Etymology Tree",
) -> Path:
    """Renders and saves a standalone interactive HTML conlang etymology tree visualizer."""
    out_path = Path(output_path).resolve()
    svg = render_etymology_tree_svg(lexemes, width=width, height=height, theme=theme)

    roots_count = sum(1 for lx in lexemes if not lx.etymology or not (">" in lx.etymology or "<" in lx.etymology))
    deriv_count = sum(1 for lx in lexemes if lx.etymology and (">" in lx.etymology or "<" in lx.etymology))
    pos_types = len({lx.part_of_speech for lx in lexemes if lx.part_of_speech})

    cards = [
        {"label": "Total Lexemes", "value": f"{len(lexemes):,}"},
        {"label": "Root Words", "value": f"{roots_count:,}"},
        {"label": "Derived Terms", "value": f"{deriv_count:,}"},
        {"label": "Parts of Speech", "value": f"{pos_types:,}"},
    ]

    html_doc = wrap_svg_in_standalone_html(
        svg_content=svg,
        title=title,
        subtitle=f"{len(lexemes)} Lexemes Indexed across {pos_types} Grammatical Category(ies)",
        metadata_cards=cards,
        default_theme=theme,
    )
    atomic_write(out_path, html_doc)
    return out_path


__all__ = [
    "export_etymology_tree_html",
    "export_orbital_calendar_html",
    "wrap_svg_in_standalone_html",
]
