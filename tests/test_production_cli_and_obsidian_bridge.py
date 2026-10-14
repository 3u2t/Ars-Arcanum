"""Production CLI Dispatch, Vault Auto-Loader, and Live Obsidian Bridge Test Suite.

Verifies:
1. All 12 new modules in `scripts/lib/` expose working `main(argv)` CLI entrypoints.
2. `DISPATCH_TABLE` in `scripts/lib/cli_handlers.py` maps all new commands (`sprint-effort`,
   `braid`, `conlang-check`, `timeline-audit`, `ledger-audit`, `validate-epistemic`,
   `continuity-suite`, `obsidian-dashboard`, `docx-tracked`, `diff-fast`, `vault-index`,
   `typed-constitution`, `plugin-sandbox`) while preserving all legacy `pruned_*` keys.
3. `vault_continuity_runner.py` scans a full Markdown World Bible + Manuscript vault end-to-end
   and writes a valid `_Arcanum_Diagnostics.md` Obsidian Callout Dashboard note.
"""

from __future__ import annotations

import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
_LIB_DIR = _SCRIPTS_DIR / "lib"
for _p in (str(_REPO_ROOT), str(_SCRIPTS_DIR), str(_LIB_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cli_handlers
import conlang_linter
import diff_core
import docx_tracked_changes
import epistemic_firewall
import narrative_braid
import phase_effort_engine
import resource_ledger
import timeline_solver
import typed_constitution
import vault_continuity_runner
from vault_index import atomic_write
import vault_index


class TestProductionCLIAndObsidianBridge(unittest.TestCase):
    """End-to-end verification of CLI entrypoints, dispatch table, and Obsidian vault bridge."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.vault = Path(self._tmp.name) / "ReliquaryUniverse"
        self.vault.mkdir(parents=True, exist_ok=True)

        atomic_write(
            self.vault / "world.yaml",
            "---\ncalendar_name: Reliquary Solar Reckoning\nmonth_lengths: [36, 36, 36, 36, 36, 36, 36, 36, 36, 36]\n---\n",
        )
        atomic_write(
            self.vault / "Characters" / "Kael.md",
            "---\nname: Kael\ntype: character\nknows: [desert_routes]\nresource_pools: {ether_vials: 4}\n---\nKael of the Sand Sea.\n",
        )
        atomic_write(
            self.vault / "Locations" / "DuneRoute.md",
            "---\ntype: route\norigin: Sunken Citadel\ndestination: Glass Oasis\ndistance_km: 120\nterrain: sand_sea\n---\n",
        )
        atomic_write(
            self.vault / "Book-01" / "Draft-01" / "01_Chapter.md",
            "---\nchapter: 1\ntitle: Dune Crossing\npov: Kael\nlocation: Sunken Citadel\n"
            "year: 1042\nmonth: 1\nday: 1\ntravel_mode: camel_caravan\n"
            "references: [desert_routes]\nlearns: [citadel_key]\n"
            "state_delta: {ether_vials: -1}\n---\n"
            '"We march at dawn," Kael said across the dunes.\n',
        )
        atomic_write(
            self.vault / "Book-01" / "Draft-01" / "02_Chapter.md",
            "---\nchapter: 2\ntitle: Arrival at the Oasis\npov: Kael\nlocation: Glass Oasis\n"
            "year: 1042\nmonth: 1\nday: 8\ntravel_mode: camel_caravan\n"
            "references: [citadel_key]\nstate_delta: {ether_vials: -1}\n---\n"
            "They reached the [[Glass Oasis]] after seven days.\n",
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_dispatch_table_wires_all_new_and_legacy_commands(self) -> None:
        table = cli_handlers.DISPATCH_TABLE
        for cmd in (
            "sprint-effort",
            "effort",
            "braid",
            "narrative-braid",
            "conlang-check",
            "timeline-audit",
            "ledger-audit",
            "validate-epistemic",
            "epistemic",
            "continuity-suite",
            "obsidian-dashboard",
            "docx-tracked",
            "diff-fast",
            "vault-index",
            "typed-constitution",
            "plugin-sandbox",
        ):
            self.assertIn(cmd, table)
            self.assertEqual(table[cmd][0], "module")

        for pruned_cmd in ("astro", "climate", "calendar", "timeline", "conlang", "magic"):
            self.assertIn(pruned_cmd, table)
            self.assertEqual(table[pruned_cmd][0], "handler")

    def test_end_to_end_vault_continuity_suite_and_obsidian_dashboard(self) -> None:
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            rc = vault_continuity_runner.main([str(self.vault)])
        self.assertEqual(rc, 0)
        payload = json.loads(buf.getvalue())
        self.assertTrue(payload["passed"])
        self.assertGreaterEqual(payload["documents_indexed"], 4)

        dash_file = self.vault / "_Arcanum_Diagnostics.md"
        self.assertTrue(dash_file.exists())
        dash_text = dash_file.read_text(encoding="utf-8")
        self.assertIn("[!success] Ars Arcanum Continuity Compiler — PASS", dash_text)

    def test_individual_cli_entrypoints_execute_cleanly(self) -> None:
        for mod, argv in (
            (vault_index, [str(self.vault)]),
            (epistemic_firewall, [str(self.vault)]),
            (timeline_solver, [str(self.vault)]),
            (resource_ledger, [str(self.vault)]),
            (narrative_braid, [str(self.vault)]),
            (conlang_linter, ["--language", "SandTongue", "kaleth", "thos"]),
            (typed_constitution, []),
            (
                phase_effort_engine,
                [
                    "--workspace",
                    str(self.vault),
                    "--book",
                    "Prisoner of Sand Sea",
                    "--draft",
                    "2000",
                ],
            ),
            (
                diff_core,
                [
                    str(self.vault / "Book-01" / "Draft-01" / "01_Chapter.md"),
                    str(self.vault / "Book-01" / "Draft-01" / "02_Chapter.md"),
                ],
            ),
        ):
            buf = io.StringIO()
            with patch("sys.stdout", buf):
                rc = mod.main(argv)
            self.assertEqual(rc, 0, f"Module {mod.__name__} failed with rc={rc}: {buf.getvalue()}")
            parsed = json.loads(buf.getvalue())
            self.assertIsInstance(parsed, dict)

        docx_out = self.vault / "ch1.docx"
        md_pulled = self.vault / "ch1_pulled.md"
        with patch("sys.stdout", io.StringIO()):
            rc_exp = docx_tracked_changes.main(
                ["export", str(self.vault / "Book-01" / "Draft-01" / "01_Chapter.md"), str(docx_out)]
            )
            rc_pull = docx_tracked_changes.main(["pull", str(docx_out), str(md_pulled)])
        self.assertEqual(rc_exp, 0)
        self.assertEqual(rc_pull, 0)
        self.assertTrue(md_pulled.exists())


if __name__ == "__main__":
    unittest.main()
