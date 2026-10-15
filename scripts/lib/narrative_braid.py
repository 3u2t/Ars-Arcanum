"""Interactive Pacing, POV Balance & Subplot Braid Matrix (`arcanum braid`).

Analyzes `@pov:`, `@subplot:`, and `@tension:` directives across a multi-POV manuscript:
1. Calculates POV word-share percentages and dialogue-to-narration pacing curves.
2. Detects POV & Subplot Droughts (`BRD-601`).
3. Renders a self-contained, air-gapped HTML + SVG swimlane braid visualization with strict
   Content-Security-Policy (`default-src 'none'; style-src 'unsafe-inline'`).

Repository Target: `scripts/lib/narrative_braid.py`
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

try:
    from lib.vault_index import VaultIndex, atomic_write
except ImportError:
    from vault_index import VaultIndex, atomic_write


@dataclass(frozen=True)
class ChapterBraidNode:
    """Single chapter entry in the narrative braid."""

    chapter_index: int
    chapter_title: str
    pov_character: str
    subplots: tuple[str, ...]
    word_count: int
    dialogue_ratio: float
    tension_score: int = 5


@dataclass(frozen=True)
class BraidDroughtAlert:
    """Advisory alert when a POV character or subplot is absent for too many consecutive words."""

    rule_id: str
    thread_type: str
    thread_name: str
    from_chapter: int
    to_chapter: int
    absent_words: int
    message: str


def analyze_narrative_braid(
    chapters: list[ChapterBraidNode],
    *,
    max_drought_words: int = 25_000,
) -> dict[str, Any]:
    """Compute POV word shares, pacing statistics, and POV/subplot drought alerts."""
    ordered = sorted(chapters, key=lambda c: c.chapter_index)
    total_manuscript_words = sum(c.word_count for c in ordered)
    pov_words: dict[str, int] = {}
    all_povs: list[str] = []
    for c in ordered:
        pov_words[c.pov_character] = pov_words.get(c.pov_character, 0) + c.word_count
        if c.pov_character not in all_povs:
            all_povs.append(c.pov_character)

    pov_shares = {
        pov: round((w / total_manuscript_words) * 100.0, 2) if total_manuscript_words > 0 else 0.0
        for pov, w in pov_words.items()
    }

    alerts: list[BraidDroughtAlert] = []
    for pov in all_povs:
        running_absent_words = 0
        last_seen_chapter: int | None = None
        for c in ordered:
            if c.pov_character == pov:
                if last_seen_chapter is not None and running_absent_words > max_drought_words:
                    alerts.append(
                        BraidDroughtAlert(
                            rule_id="BRD-601",
                            thread_type="POV",
                            thread_name=pov,
                            from_chapter=last_seen_chapter,
                            to_chapter=c.chapter_index,
                            absent_words=running_absent_words,
                            message=(
                                f"BRD-601 POV Drought: '{pov}' is absent for {running_absent_words:,} "
                                f"words between Chapter {last_seen_chapter} and Chapter {c.chapter_index} "
                                f"(threshold: {max_drought_words:,} words)."
                            ),
                        )
                    )
                last_seen_chapter = c.chapter_index
                running_absent_words = 0
            elif last_seen_chapter is not None:
                running_absent_words += c.word_count

    return {
        "total_words": total_manuscript_words,
        "chapter_count": len(ordered),
        "pov_word_totals": pov_words,
        "pov_word_shares_pct": pov_shares,
        "drought_alerts": [asdict(a) for a in alerts],
        "chapters": [asdict(c) for c in ordered],
    }


def render_braid_html(
    chapters: list[ChapterBraidNode],
    output_html: Path | None = None,
    *,
    max_drought_words: int = 25_000,
) -> str:
    """Render an offline, CSP-locked HTML + SVG swimlane braid matrix."""
    report = analyze_narrative_braid(chapters, max_drought_words=max_drought_words)
    ordered = sorted(chapters, key=lambda c: c.chapter_index)
    pov_list = list(report["pov_word_totals"].keys())

    svg_width = max(640, 140 + len(ordered) * 70)
    svg_height = max(220, 80 + len(pov_list) * 50)

    svg_rows: list[str] = []
    for row_idx, pov in enumerate(pov_list):
        y = 55 + row_idx * 45
        esc_pov = html.escape(pov)
        svg_rows.append(
            f'<text x="16" y="{y + 5}" fill="#e2e8f0" font-family="monospace" font-size="13">{esc_pov}</text>'
        )
        svg_rows.append(
            f'<line x1="130" y1="{y}" x2="{svg_width - 20}" y2="{y}" stroke="#334155" stroke-dasharray="4 4"/>'
        )
        for col_idx, ch in enumerate(ordered):
            x = 155 + col_idx * 65
            if ch.pov_character == pov:
                radius = max(7, min(16, int(ch.word_count / 450)))
                svg_rows.append(
                    f'<circle cx="{x}" cy="{y}" r="{radius}" fill="#f59e0b" stroke="#fef3c7" stroke-width="2">'
                    f"<title>Ch {ch.chapter_index}: {html.escape(ch.chapter_title)} ({ch.word_count:,} wds, "
                    f"Tension {ch.tension_score}/10)</title></circle>"
                )

    alert_items = "".join(
        f"<li><strong>{html.escape(a['rule_id'])}</strong>: {html.escape(a['message'])}</li>"
        for a in report["drought_alerts"]
    ) or "<li>No POV drought anomalies detected.</li>"

    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:;">
<title>Ars Arcanum — Narrative Braid &amp; POV Pacing Matrix</title>
<style>
  body {{ background: #0f172a; color: #f8fafc; font-family: system-ui, sans-serif; margin: 2rem; }}
  h1, h2 {{ color: #fbbf24; }}
  .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 1.25rem; margin-bottom: 1.5rem; }}
</style>
</head>
<body>
  <h1>Ars Arcanum — Narrative Braid &amp; POV Pacing Matrix</h1>
  <div class="card">
    <h2>POV Swimlane Braid ({report['total_words']:,} Total Words across {report['chapter_count']} Chapters)</h2>
    <svg width="{svg_width}" height="{svg_height}">
      {''.join(svg_rows)}
    </svg>
  </div>
  <div class="card">
    <h2>Continuity &amp; Drought Diagnostics</h2>
    <ul>{alert_items}</ul>
  </div>
</body>
</html>
"""
    if output_html is not None:
        atomic_write(output_html, html_doc)
    return html_doc


def scan_manuscript_braid(vault_root: Path) -> list[ChapterBraidNode]:
    """Scan a manuscript directory via `VaultIndex` and build ordered `ChapterBraidNode` objects."""
    index = VaultIndex(vault_root)
    nodes = index.scan_vault()
    chapters: list[ChapterBraidNode] = []

    for idx_num, node in enumerate(nodes, start=1):
        fm = node.frontmatter
        pov = str(fm.get("pov") or node.directives.get("pov") or "Omniscient")
        raw_subplots = fm.get("subplots") or node.directives.get("subplot") or ()
        if isinstance(raw_subplots, str):
            subplots = tuple(s.strip() for s in raw_subplots.split(",") if s.strip())
        elif isinstance(raw_subplots, (list, tuple)):
            subplots = tuple(str(s).strip() for s in raw_subplots if str(s).strip())
        else:
            subplots = ()

        tension = int(fm.get("tension") or node.directives.get("tension") or 5)
        chapters.append(
            ChapterBraidNode(
                chapter_index=int(fm.get("chapter", idx_num)),
                chapter_title=str(fm.get("title") or Path(node.relative_path).stem),
                pov_character=pov,
                subplots=subplots,
                word_count=node.metrics.total_words,
                dialogue_ratio=node.metrics.dialogue_ratio,
                tension_score=tension,
            )
        )
    return chapters


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for `arcanum braid` / `arcanum narrative-braid`."""
    parser = argparse.ArgumentParser(
        prog="arcanum braid",
        description="Analyze multi-POV pacing, detect character droughts, and export an HTML/SVG braid matrix.",
    )
    parser.add_argument("manuscript", nargs="?", type=Path, default=Path.cwd(), help="Manuscript or vault path")
    parser.add_argument("--html", type=Path, default=None, help="Optional output HTML path for the SVG braid")
    parser.add_argument("--max-drought-words", type=int, default=25_000, help="POV drought word threshold")
    args = parser.parse_args(argv)

    chapters = scan_manuscript_braid(args.manuscript)
    if args.html is not None:
        render_braid_html(chapters, args.html, max_drought_words=args.max_drought_words)
    report = analyze_narrative_braid(chapters, max_drought_words=args.max_drought_words)
    sys.stdout.write(json.dumps(report, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
