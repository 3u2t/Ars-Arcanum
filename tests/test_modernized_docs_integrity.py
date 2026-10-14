"""Verification test suite ensuring modernized documentation satisfies all repository doc invariants."""

from __future__ import annotations

from pathlib import Path
import re
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestModernizedDocsIntegrity(unittest.TestCase):
    """Verifies governance, sustainability, threat-model, agentic-doctrine, and changelog invariants."""

    def test_governance_and_sustainability_headings(self) -> None:
        gov_text = (REPO_ROOT / "docs" / "GOVERNANCE.md").read_text(encoding="utf-8")
        for heading in (
            "Governance Principles",
            "Roles & Responsibilities",
            "Decision-Making & RFC Process",
            "Release Cadence & Versioning",
            "Security & Vulnerability Disclosure",
        ):
            self.assertIn(heading, gov_text)

        sust_text = (REPO_ROOT / "docs" / "SUSTAINABILITY.md").read_text(encoding="utf-8")
        for heading in (
            "Independence & Freedom Pledge",
            "Funding Streams & Financial Stewardship",
            "GitHub Sponsors",
        ):
            self.assertIn(heading, sust_text)

    def test_agentic_doctrine_and_roadmap_queues(self) -> None:
        agents_text = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        for contract in (
            "Atomic Writes",
            "Cross-Platform File Locking",
            "Path Traversal Defense",
            "Zero-Pip Dependency Guarantee",
            "Content-Security-Policy",
        ):
            self.assertIn(contract, agents_text)

        roadmap_text = (REPO_ROOT / "docs" / "ROADMAP.md").read_text(encoding="utf-8")
        for queue in ("`now`", "`next`", "`blocked`", "`improve`", "`recurring`"):
            self.assertIn(queue, agents_text)
            self.assertIn(queue, roadmap_text)

    def test_threat_model_stride_sections(self) -> None:
        threat_text = (REPO_ROOT / "docs" / "THREAT_MODEL.md").read_text(encoding="utf-8")
        for section in (
            "STRIDE-Lite",
            "Spoofing Identity",
            "Tampering with Data",
            "Repudiation",
            "Information Disclosure",
            "Denial of Service",
            "Elevation of Privilege",
            "Content Security Policy",
        ):
            self.assertIn(section, threat_text)

    def test_changelog_version_header_matches_0_1_0(self) -> None:
        changelog = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        match = re.search(r"##\s*\[([0-9.]+)\]", changelog)
        self.assertIsNotNone(match)
        if match is not None:
            self.assertEqual(match.group(1), "0.1.0")


if __name__ == "__main__":
    unittest.main()
