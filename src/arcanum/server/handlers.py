"""HTTP Request Handlers for Ars Arcanum Sovereign Studio Server.

Provides air-gapped local endpoints for the visual web studio and Obsidian companion plugin.
Zero-pip standard library implementation.
"""

from __future__ import annotations

import html
import http.server
import json
import logging
from pathlib import Path
import time
from typing import Any
import urllib.parse

from scripts.lib.conlang_linter import ConlangLexeme, import_polyglot_lexicon, render_etymology_tree_svg
from scripts.lib.narrative_braid import render_braid_html, scan_manuscript_braid
from scripts.lib.phase_effort_engine import PhaseEffortLedger
from scripts.lib.portfolio import scan_portfolio
from scripts.lib.publisher import publish_manuscript
from scripts.lib.timeline_solver import CustomCalendarSpec, render_orbital_calendar_svg
from scripts.lib.typed_constitution import load_yaml_constitution_file
from scripts.lib.vault_continuity_runner import run_full_vault_continuity_suite
from scripts.lib.vault_index import atomic_write, parse_frontmatter

logger = logging.getLogger("arcanum.server")


class ArcanumStudioHandler(http.server.BaseHTTPRequestHandler):
    """Zero-pip HTTP handler serving Arcanum Studio API and UI."""

    vault_root: Path = Path.cwd()
    studio_html_path: Path = Path(__file__).resolve().parent.parent / "ui" / "studio_app.html"
    active_sprint: dict[str, Any] | None = None
    session_token: str | None = None

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress standard logging to keep terminal output clean."""

    def _is_authorized(self, parsed_url: urllib.parse.ParseResult) -> bool:
        """Check if request contains valid token when session_token is configured."""
        if self.session_token is None:
            return True
        header_token = self.headers.get("X-Arcanum-Token")
        if header_token == self.session_token:
            return True
        q = urllib.parse.parse_qs(parsed_url.query)
        return q.get("token", [None])[0] == self.session_token

    def _set_headers(self, content_type: str = "application/json", status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Arcanum-Token")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Arcanum-Token")
        self.end_headers()

    def do_GET(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if path in ("", "/", "/studio"):
            self._serve_studio_html()
            return

        if path.startswith("/api/") and not self._is_authorized(parsed_url):
            self._set_headers(status=401)
            self.wfile.write(json.dumps({"error": "Unauthorized: valid X-Arcanum-Token required"}).encode("utf-8"))
            return

        if path == "/api/status":
            self._set_headers()
            payload = {
                "status": "ok",
                "version": "0.1.0",
                "vault": str(self.vault_root),
                "has_active_sprint": self.active_sprint is not None,
            }
            self.wfile.write(json.dumps(payload).encode("utf-8"))
            return

        if path == "/api/portfolio":
            self._set_headers()
            try:
                report = scan_portfolio(self.vault_root)
                self.wfile.write(json.dumps(report).encode("utf-8"))
            except Exception as e:
                self.wfile.write(json.dumps({"error": str(e), "projects": []}).encode("utf-8"))
            return

        if path == "/api/diagnostics":
            self._set_headers()
            try:
                report = run_full_vault_continuity_suite(self.vault_root, write_obsidian_dashboard=True)
                self.wfile.write(json.dumps(report).encode("utf-8"))
            except Exception as e:
                self.wfile.write(json.dumps({"error": str(e), "passed": False}).encode("utf-8"))
            return

        if path == "/api/visualizers/calendar":
            q = urllib.parse.parse_qs(parsed_url.query)
            theme = q.get("theme", ["dark"])[0]
            fmt = q.get("format", ["svg"])[0].lower()
            try:
                width = int(q.get("width", ["640"])[0])
                height = int(q.get("height", ["640"])[0])
            except (ValueError, TypeError):
                width, height = 640, 640
            cal_spec = self._load_calendar_spec(self.vault_root)
            if fmt == "html":
                from src.arcanum.worldbible.visualizers import wrap_svg_in_standalone_html
                svg = render_orbital_calendar_svg(cal_spec, width=width, height=height, theme=theme)
                month_min = min(cal_spec.month_lengths) if cal_spec.month_lengths else 0
                month_max = max(cal_spec.month_lengths) if cal_spec.month_lengths else 0
                month_range = f"{month_min}d" if month_min == month_max else f"{month_min}–{month_max}d"
                cards = [
                    {"label": "Days Per Year", "value": f"{cal_spec.days_per_year:,}"},
                    {"label": "Months", "value": f"{len(cal_spec.month_lengths)}"},
                    {"label": "Calendar Name", "value": cal_spec.calendar_name},
                    {"label": "Month Lengths", "value": month_range},
                ]
                html_doc = wrap_svg_in_standalone_html(
                    svg_content=svg,
                    title=f"{cal_spec.calendar_name} — Planetary Orbital Calendar",
                    subtitle=f"{len(cal_spec.month_lengths)} Months · {cal_spec.days_per_year} Days per Orbital Revolution",
                    metadata_cards=cards,
                    default_theme=theme,
                )
                self._set_headers(content_type="text/html; charset=utf-8")
                self.wfile.write(html_doc.encode("utf-8"))
                return
            svg = render_orbital_calendar_svg(cal_spec, width=width, height=height, theme=theme)
            self._set_headers(content_type="image/svg+xml")
            self.wfile.write(svg.encode("utf-8"))
            return

        if path == "/api/visualizers/etymology":
            q = urllib.parse.parse_qs(parsed_url.query)
            theme = q.get("theme", ["dark"])[0]
            fmt = q.get("format", ["svg"])[0].lower()
            try:
                width = int(q.get("width", ["800"])[0])
                height = int(q.get("height", ["500"])[0])
            except (ValueError, TypeError):
                width, height = 800, 500
            lexemes = self._load_conlang_lexemes(self.vault_root)
            if fmt == "html":
                from src.arcanum.worldbible.visualizers import wrap_svg_in_standalone_html
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
                    title="PolyGlot Conlang Etymology Tree",
                    subtitle=f"{len(lexemes)} Lexemes Indexed across {pos_types} Grammatical Category(ies)",
                    metadata_cards=cards,
                    default_theme=theme,
                )
                self._set_headers(content_type="text/html; charset=utf-8")
                self.wfile.write(html_doc.encode("utf-8"))
                return
            svg = render_etymology_tree_svg(lexemes, width=width, height=height, theme=theme)
            self._set_headers(content_type="image/svg+xml")
            self.wfile.write(svg.encode("utf-8"))
            return

        if path == "/api/visualizers/braid":
            q = urllib.parse.parse_qs(parsed_url.query)
            sort_by = q.get("sort_by", ["manuscript"])[0]
            try:
                chapters = scan_manuscript_braid(self.vault_root)
                html_doc = render_braid_html(chapters, sort_by=sort_by)
                self._set_headers(content_type="text/html; charset=utf-8")
                self.wfile.write(html_doc.encode("utf-8"))
            except Exception as e:
                self._set_headers(content_type="application/json", status=500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        self._set_headers("text/plain", 404)
        self.wfile.write(b"Not Found")

    @classmethod
    def _load_calendar_spec(cls, vault_root: Path) -> CustomCalendarSpec:
        world_yaml = vault_root / "world.yaml"
        if not world_yaml.is_file():
            ms_yaml = vault_root / "manuscript.yaml"
            if not ms_yaml.is_file() and (vault_root.parent / "manuscript.yaml").is_file():
                ms_yaml = vault_root.parent / "manuscript.yaml"
            if ms_yaml.is_file():
                try:
                    ms_raw = ms_yaml.read_text(encoding="utf-8")
                    wrapped = ms_raw if ms_raw.lstrip().startswith("---") else f"---\n{ms_raw}\n---\n"
                    ms_meta, _ = parse_frontmatter(wrapped)
                    uni_path_str = ms_meta.get("universe") or ms_meta.get("world_bible")
                    if uni_path_str:
                        cand = (ms_yaml.parent / str(uni_path_str) / "world.yaml").resolve()
                        if cand.is_file():
                            world_yaml = cand
                except Exception:
                    pass

        cal_name = "Standard Solar Reckoning"
        month_lengths: tuple[int, ...] = (30,) * 12
        month_names: tuple[str, ...] = tuple(f"Month-{i}" for i in range(1, 13))

        if world_yaml.is_file():
            try:
                raw = world_yaml.read_text(encoding="utf-8")
                wrapped = raw if raw.lstrip().startswith("---") else f"---\n{raw}\n---\n"
                meta, _ = parse_frontmatter(wrapped)
                if "calendar_name" in meta:
                    cal_name = str(meta["calendar_name"])
                if isinstance(meta.get("month_lengths"), list) and meta["month_lengths"]:
                    month_lengths = tuple(int(x) for x in meta["month_lengths"])
                if isinstance(meta.get("month_names"), list) and meta["month_names"]:
                    month_names = tuple(str(x) for x in meta["month_names"])
                else:
                    month_names = tuple(f"Month-{i}" for i in range(1, len(month_lengths) + 1))
            except Exception:
                pass

        return CustomCalendarSpec(
            calendar_name=cal_name,
            month_names=month_names,
            month_lengths=month_lengths,
        )

    @classmethod
    def _load_conlang_lexemes(cls, vault_root: Path) -> list[ConlangLexeme]:
        candidates = [
            vault_root / "Languages",
            vault_root / "WorldBible" / "Languages",
            vault_root / "World_Bible" / "Languages",
        ]
        ms_yaml = vault_root / "manuscript.yaml"
        if not ms_yaml.is_file() and (vault_root.parent / "manuscript.yaml").is_file():
            ms_yaml = vault_root.parent / "manuscript.yaml"
        if ms_yaml.is_file():
            try:
                ms_raw = ms_yaml.read_text(encoding="utf-8")
                wrapped = ms_raw if ms_raw.lstrip().startswith("---") else f"---\n{ms_raw}\n---\n"
                ms_meta, _ = parse_frontmatter(wrapped)
                uni_path_str = ms_meta.get("universe") or ms_meta.get("world_bible")
                if uni_path_str:
                    cand_uni = (ms_yaml.parent / str(uni_path_str)).resolve()
                    if cand_uni.is_dir():
                        candidates.extend([
                            cand_uni / "Languages",
                            cand_uni / "WorldBible" / "Languages",
                        ])
            except Exception:
                pass

        lexemes: list[ConlangLexeme] = []
        for cand_dir in candidates:
            if cand_dir.is_dir():
                for f in sorted(cand_dir.iterdir()):
                    if f.is_file() and f.suffix.lower() in (".pgd", ".xml"):
                        try:
                            lexemes.extend(import_polyglot_lexicon(f))
                        except Exception:
                            pass
        return lexemes

    def do_POST(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if path.startswith("/api/") and not self._is_authorized(parsed_url):
            self._set_headers(status=401)
            self.wfile.write(json.dumps({"error": "Unauthorized: valid X-Arcanum-Token required"}).encode("utf-8"))
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            payload = {}

        if path == "/api/sprint/start":
            ArcanumStudioHandler.active_sprint = {
                "started_at": time.time(),
                "duration_minutes": float(payload.get("minutes", 25)),
                "target_words": int(payload.get("target", 500)),
                "project": str(payload.get("project", "")),
            }
            self._set_headers()
            self.wfile.write(json.dumps({"status": "started", "sprint": self.active_sprint}).encode("utf-8"))
            return

        if path == "/api/sprint/stop":
            sprint_data = ArcanumStudioHandler.active_sprint
            ArcanumStudioHandler.active_sprint = None
            if sprint_data:
                try:
                    ledger = PhaseEffortLedger(self.vault_root)
                    mins = max(1.0, (time.time() - sprint_data["started_at"]) / 60.0)
                    ledger.log_session(
                        words_delta=sprint_data["target_words"],
                        duration_minutes=round(mins, 1),
                        stage="Drafting",
                        notes=f"Sprint completed via Arcanum Studio ({round(mins, 1)}m)",
                    )
                except Exception as e:
                    logger.debug("Failed logging session to ledger: %s", e)

            self._set_headers()
            self.wfile.write(json.dumps({"status": "stopped", "logged": sprint_data is not None}).encode("utf-8"))
            return

        if path == "/api/constitution/allow":
            rule_id = str(payload.get("rule_id", "")).strip()
            if not rule_id:
                self._set_headers(status=400)
                self.wfile.write(json.dumps({"error": "rule_id is required"}).encode("utf-8"))
                return

            const_path = self.vault_root / "constitution.yaml"
            current_dict = load_yaml_constitution_file(const_path) if const_path.is_file() else {}
            rules = list(current_dict.get("rules", []))
            neg_rule = f"!{rule_id}"
            if neg_rule not in rules:
                rules.append(neg_rule)
                current_dict["rules"] = rules

            # Write back cleanly
            yaml_lines = ["---", "rules:"]
            for r in rules:
                yaml_lines.append(f"  - '{r}'")
            yaml_lines.append("---\n")
            atomic_write(const_path, "\n".join(yaml_lines))

            self._set_headers()
            self.wfile.write(json.dumps({"status": "allowed", "rule_id": rule_id, "active_rules": rules}).encode("utf-8"))
            return

        if path == "/api/action/export":
            fmt = str(payload.get("format", "docx")).lower()
            ms_dir = self.vault_root
            if (self.vault_root / "Manuscript").is_dir():
                ms_sub = list((self.vault_root / "Manuscript").iterdir())
                if ms_sub:
                    ms_dir = ms_sub[0]

            try:
                res = publish_manuscript(ms_dir, output_format=fmt, inspect_only=False)
                self._set_headers()
                self.wfile.write(json.dumps(res).encode("utf-8"))
            except Exception as e:
                self._set_headers(status=500)
                self.wfile.write(json.dumps({"status": "error", "reason": str(e)}).encode("utf-8"))
            return

        self._set_headers("text/plain", 404)
        self.wfile.write(b"Not Found")

    def _serve_studio_html(self) -> None:
        if not self.studio_html_path.is_file():
            self._set_headers("text/plain", 404)
            self.wfile.write(b"Studio HTML template not found on disk.")
            return

        content = self.studio_html_path.read_bytes()
        if self.session_token:
            token_meta = f'<meta name="arcanum-token" content="{html.escape(self.session_token)}">\n'.encode()
            content = content.replace(b"<head>", b"<head>\n  " + token_meta, 1)
        self._set_headers("text/html; charset=utf-8")
        self.wfile.write(content)
