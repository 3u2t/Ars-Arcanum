"""Unit tests for Ars Arcanum Sovereign Web Studio Server & REST API."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
import urllib.request
import urllib.error

from scripts.lib.vault_index import atomic_write
from src.arcanum.server.daemon import start_studio_daemon


class TestStudioServer(unittest.TestCase):
    """Verify HTTP endpoints and REST handlers of the local studio server."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls._tmp.name)
        # Seed basic manuscript & chapter
        ms_dir = cls.root / "Manuscript" / "Novel-A" / "Draft-01"
        ms_dir.mkdir(parents=True, exist_ok=True)
        atomic_write(
            ms_dir / "01_Chapter.md",
            "---\ntitle: The First Oasis\npov: Kael\n---\nKael crossed the golden expanse of the dunes.\n",
        )
        # Port 4249 for testing to avoid conflicts
        cls.port = 4249
        cls.server = start_studio_daemon(cls.root, port=cls.port, open_browser=False, block=False)
        cls.base_url = f"http://127.0.0.1:{cls.port}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls._tmp.cleanup()

    @classmethod
    def _make_req(
        cls,
        path: str,
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> urllib.request.Request:
        url = f"{cls.base_url}{path}"
        return urllib.request.Request(url, data=data, headers=headers or {})  # noqa: S310

    @staticmethod
    def _open_url(req: urllib.request.Request | str):
        return urllib.request.urlopen(req)  # noqa: S310

    def test_status_endpoint(self) -> None:
        req = self._make_req("/api/status")
        with self._open_url(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["status"], "ok")
            self.assertEqual(data["version"], "0.1.0")

    def test_studio_html_endpoint(self) -> None:
        req = self._make_req("/studio")
        with self._open_url(req) as resp:
            self.assertEqual(resp.status, 200)
            content = resp.read().decode("utf-8")
            self.assertIn("Ars Arcanum Studio", content)
            self.assertIn("Content-Security-Policy", content)

    def test_portfolio_endpoint(self) -> None:
        req = self._make_req("/api/portfolio")
        with self._open_url(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("projects", data)

    def test_diagnostics_endpoint(self) -> None:
        req = self._make_req("/api/diagnostics")
        with self._open_url(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("passed", data)
            self.assertIn("epistemic", data)

    def test_sprint_start_and_stop_lifecycle(self) -> None:
        start_payload = json.dumps({"minutes": 15, "target": 350}).encode("utf-8")
        start_req = self._make_req(
            "/api/sprint/start",
            data=start_payload,
            headers={"Content-Type": "application/json"},
        )
        with self._open_url(start_req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["status"], "started")
            self.assertEqual(data["sprint"]["target_words"], 350)

        stop_req = self._make_req(
            "/api/sprint/stop",
            data=b"{}",
            headers={"Content-Type": "application/json"},
        )
        with self._open_url(stop_req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["status"], "stopped")
            self.assertTrue(data["logged"])

    def test_constitution_allow_rule_action(self) -> None:
        payload = json.dumps({"rule_id": "EPI-201"}).encode("utf-8")
        req = self._make_req(
            "/api/constitution/allow",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with self._open_url(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["status"], "allowed")
            self.assertIn("!EPI-201", data["active_rules"])

        const_file = self.root / "constitution.yaml"
        self.assertTrue(const_file.exists())
        self.assertIn("!EPI-201", const_file.read_text(encoding="utf-8"))

    def test_constitution_allow_empty_rule_id_returns_400(self) -> None:
        payload = json.dumps({"rule_id": ""}).encode("utf-8")
        req = self._make_req(
            "/api/constitution/allow",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self._open_url(req)
        self.assertEqual(ctx.exception.code, 400)
        ctx.exception.close()

    def test_options_cors_preflight(self) -> None:
        req = self._make_req("/api/status")
        req.get_method = lambda: "OPTIONS"  # type: ignore[assignment]
        with self._open_url(req) as resp:
            self.assertEqual(resp.status, 204)
            self.assertEqual(resp.headers.get("Access-Control-Allow-Origin"), "*")

    def test_not_found_get_and_post(self) -> None:
        get_req = self._make_req("/api/nonexistent")
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self._open_url(get_req)
        self.assertEqual(ctx.exception.code, 404)
        ctx.exception.close()

        post_req = self._make_req("/api/nonexistent", data=b"{}")
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self._open_url(post_req)
        self.assertEqual(ctx.exception.code, 404)
        ctx.exception.close()

    def test_export_action_endpoint(self) -> None:
        payload = json.dumps({"format": "markdown"}).encode("utf-8")
        req = self._make_req(
            "/api/action/export",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with self._open_url(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("status", data)

    def test_studio_server_compatibility_bridge(self) -> None:
        from scripts.lib import studio_server
        self.assertTrue(callable(studio_server.main))
        self.assertTrue(callable(studio_server.start_studio_daemon))

    def test_daemon_cli_parser(self) -> None:
        from src.arcanum.server.daemon import main
        # Run with --help or invalid flag to test parser exit without hanging
        with self.assertRaises(SystemExit) as ctx:
            main(["--help"])
        self.assertEqual(ctx.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
