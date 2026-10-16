"""Unit tests for Federated Series Continuity across Multi-Vault Universes (Level 6)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.lib.epistemic_firewall import audit_vault_epistemic
from scripts.lib.resource_ledger import audit_vault_resources
from scripts.lib.timeline_solver import audit_vault_timeline
from scripts.lib.vault_continuity_runner import run_full_vault_continuity_suite
from scripts.lib.vault_index import atomic_write


class TestFederatedSeriesContinuity(unittest.TestCase):
    """Verify cross-vault federation of world bibles, constitutions, and manuscripts."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_dir = Path(self._tmp.name)

        # 1. Shared Universe Vault (~/Universes/Cosmere)
        self.universe_root = self.tmp_dir / "Universes" / "Cosmere"
        self.universe_root.mkdir(parents=True, exist_ok=True)

        # Universe Constitution: enforce strict epistemic and timeline rules
        atomic_write(
            self.universe_root / "constitution.yaml",
            "scope_name: Cosmere Universe\nrules:\n  - EPI-201\n  - TIME-301\n  - LED-501\n",
        )

        # Universe Lore: Character baseline in shared world bible
        chars_dir = self.universe_root / "Characters"
        chars_dir.mkdir(parents=True, exist_ok=True)
        atomic_write(
            chars_dir / "Kelsier.md",
            "---\nname: Kelsier\nknows:\n  - allomancy\n  - eleventh_metal\n---\nLeader of the rebellion.\n",
        )

        # Universe Lore: Custom Calendar in world.yaml
        atomic_write(
            self.universe_root / "world.yaml",
            "---\ncalendar_name: Scadrian Solar Cycle\nmonth_lengths: [28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28]\n---\n",
        )

        # Universe Lore: Route in Locations/
        locs_dir = self.universe_root / "Locations"
        locs_dir.mkdir(parents=True, exist_ok=True)
        atomic_write(
            locs_dir / "Luthadel_To_Fellside.md",
            "---\ntype: route\norigin: Luthadel\ndestination: Fellside\ndistance_km: 120\nterrain: plains\n---\nHighway.\n",
        )

        # Universe Lore: Shared Resource Pool
        magic_dir = self.universe_root / "Magic-Technology"
        magic_dir.mkdir(parents=True, exist_ok=True)
        atomic_write(
            magic_dir / "AtiumReserve.md",
            "---\nentity: Kelsier\nresource_pools:\n  atium_beads: 10\n---\nAtium stash.\n",
        )

        # 2. Manuscript Vault (~/Manuscripts/Mistborn/Draft-01)
        self.manuscript_root = self.tmp_dir / "Manuscripts" / "Mistborn" / "Draft-01"
        self.manuscript_root.mkdir(parents=True, exist_ok=True)

        # Chapter 1: Kelsier uses allomancy and atium
        atomic_write(
            self.manuscript_root / "01_Prologue.md",
            (
                "---\n"
                "title: Midnight in the Ash\n"
                "chapter: 1\n"
                "pov: Kelsier\n"
                "references: [allomancy]\n"
                "state_delta:\n"
                "  atium_beads: -2\n"
                "year: 1021\n"
                "month: 1\n"
                "day: 1\n"
                "location: Luthadel\n"
                "---\n"
                "Kelsier flared tin and tapped his [[allomancy]] to survey the misty streets.\n"
            ),
        )

        # Chapter 2: Kelsier travels to Fellside over 5 days (120 km in plains is easily doable)
        atomic_write(
            self.manuscript_root / "02_Fellside.md",
            (
                "---\n"
                "title: The Canal Crossing\n"
                "chapter: 2\n"
                "pov: Kelsier\n"
                "year: 1021\n"
                "month: 1\n"
                "day: 6\n"
                "location: Fellside\n"
                "---\n"
                "Kelsier reached Fellside after five days on the road.\n"
            ),
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_epistemic_federation_resolves_shared_character_baseline(self) -> None:
        # Without world_root, Kelsier is not defined in the manuscript directory,
        # so referencing 'allomancy' causes an EPI-201 violation
        isolated_report = audit_vault_epistemic(self.manuscript_root)
        self.assertFalse(isolated_report.passed)
        self.assertTrue(any(v.rule_id == "EPI-201" for v in isolated_report.violations))

        # With world_root pointing to shared universe, Kelsier's knowledge baseline is federated
        federated_report = audit_vault_epistemic(self.manuscript_root, world_root=self.universe_root)
        self.assertTrue(federated_report.passed)
        self.assertEqual(len(federated_report.violations), 0)

    def test_timeline_federation_resolves_shared_calendar_and_routes(self) -> None:
        # Federated timeline audit loads custom calendar and route definitions
        tl_report = audit_vault_timeline(self.manuscript_root, world_root=self.universe_root)
        self.assertEqual(tl_report["calendar_name"], "Scadrian Solar Cycle")
        self.assertEqual(tl_report["routes_loaded"], 1)
        self.assertTrue(tl_report["passed"])
        self.assertEqual(len(tl_report["anomalies"]), 0)

    def test_resource_ledger_federation_resolves_shared_pools(self) -> None:
        # Federated resource audit loads initial pool of 10 beads from shared universe
        res_report = audit_vault_resources(self.manuscript_root, world_root=self.universe_root)
        self.assertTrue(res_report["passed"])
        self.assertEqual(len(res_report["violations"]), 0)

    def test_full_continuity_suite_auto_discovery_via_manuscript_yaml(self) -> None:
        # Link shared universe in project-level manuscript.yaml
        rel_universe_path = "../../Universes/Cosmere"
        atomic_write(
            self.manuscript_root.parent / "manuscript.yaml",
            f"---\ntitle: Mistborn: The Final Empire\nuniverse: {rel_universe_path}\n---\n",
        )

        # Run continuity suite with zero explicit world_root argument
        suite_res = run_full_vault_continuity_suite(self.manuscript_root, write_obsidian_dashboard=True)

        self.assertTrue(suite_res["passed"])
        self.assertIsNotNone(suite_res["world_root"])
        self.assertEqual(Path(suite_res["world_root"]).name, "Cosmere")
        self.assertEqual(suite_res["constitution"]["scope_name"], "Cosmere Universe")

        # Verify Obsidian dashboard includes federated universe badge
        dash_path = self.manuscript_root / "_Arcanum_Diagnostics.md"
        self.assertTrue(dash_path.is_file())
        dash_content = dash_path.read_text(encoding="utf-8")
        self.assertIn("Federated Series Universe", dash_content)
        self.assertIn("Cosmere", dash_content)


if __name__ == "__main__":
    unittest.main()
