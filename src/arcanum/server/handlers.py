"""HTTP Request Handlers for Ars Arcanum Sovereign Studio Server.

Provides air-gapped local endpoints for the visual web studio and Obsidian companion plugin.
Zero-pip standard library implementation.
"""

from __future__ import annotations

import http.server
import json
import logging
from pathlib import Path
import time
from typing import Any
import urllib.parse

from scripts.lib.phase_effort_engine import PhaseEffortLedger
from scripts.lib.portfolio import scan_portfolio
from scripts.lib.publisher import publish_manuscript
from scripts.lib.typed_constitution import load_yaml_constitution_file
from scripts.lib.vault_continuity_runner import run_full_vault_continuity_suite
from scripts.lib.vault_index import atomic_write

logger = logging.getLogger("arcanum.server")


class ArcanumStudioHandler(http.server.BaseHTTPRequestHandler):
    """Zero-pip HTTP handler serving Arcanum Studio API and UI."""

    vault_root: Path = Path.cwd()
    studio_html_path: Path = Path(__file__).resolve().parent.parent / "ui" / "studio_app.html"
    active_sprint: dict[str, Any] | None = None

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress standard logging to keep terminal output clean."""

    def _set_headers(self, content_type: str = "application/json", status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if path in ("", "/", "/studio"):
            self._serve_studio_html()
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

        self._set_headers("text/plain", 404)
        self.wfile.write(b"Not Found")

    def do_POST(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

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
        self._set_headers("text/html; charset=utf-8")
        self.wfile.write(content)
