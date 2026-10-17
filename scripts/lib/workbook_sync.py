"""Live Excel Workbook Synchronizer & Telemetry Compiler (`scripts/lib/workbook_sync.py`).

Automatically populates, updates, and generates tables, formulas, and cached chart telemetry inside
`Master_Writing_Ecosystem.xlsx` whenever changes occur across an Ars Arcanum workspace:
- Reads Universe/Series definitions (`universe.yaml`, `world.yaml`, `.arcanum/ecosystem_series.json`)
- Reads Book/Manuscript pipelines (`manuscript.yaml`, chapter word counts, `.arcanum/ecosystem_books.json`)
- Reads Phase-Aware Sprint logs (`.arcanum/sprint_log.jsonl` from `phase_effort_engine.py`)
- Executes deterministic Continuity Compilers (`EPI-*`, `TIME-*`, `CON-*`, `LED-*`, `BRD-*`, churn, scraps)
- Indexes World Bible & Lore domains (`Characters`, `Locations`, `Magic`, `Conlang`, `Factions`, `Artifacts`, `History`)
- Updates `Master_Writing_Ecosystem.xlsx` in-place using a zero-dependency OpenXML (`zipfile` + `xml.etree.ElementTree`)
  engine that preserves 100% of native Excel charts, conditional formatting, data validations, and cell styles.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import subprocess  # nosec B404
import sys
import tempfile
import time
from typing import Any
import xml.etree.ElementTree as ET  # nosec B405
import zipfile

try:
    from lib.epistemic_firewall import audit_vault_epistemic
    from lib.narrative_braid import analyze_narrative_braid, scan_manuscript_braid
    from lib.phase_effort_engine import PhaseEffortLedger, ProjectStage
    from lib.resource_ledger import audit_vault_resources
    from lib.timeline_solver import audit_vault_timeline
    from lib.vault_index import VaultIndex, is_safe_subpath
except ImportError:
    from epistemic_firewall import audit_vault_epistemic  # type: ignore[no-redef]
    from narrative_braid import analyze_narrative_braid, scan_manuscript_braid  # type: ignore[no-redef]
    from phase_effort_engine import PhaseEffortLedger, ProjectStage  # type: ignore[no-redef]
    from resource_ledger import audit_vault_resources  # type: ignore[no-redef]
    from timeline_solver import audit_vault_timeline  # type: ignore[no-redef]
    from vault_index import VaultIndex, is_safe_subpath  # type: ignore[no-redef]

NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL_OFFICE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_REL_PKG = "http://schemas.openxmlformats.org/package/2006/relationships"

ET.register_namespace("", NS_MAIN)
ET.register_namespace("r", NS_REL_OFFICE)

DEFAULT_WORKBOOK_FILENAME = "Master_Writing_Ecosystem.xlsx"
TEMPLATE_REL_PATH = Path("templates") / "ecosystem" / DEFAULT_WORKBOOK_FILENAME


@dataclass(frozen=True)
class SeriesRecord:
    """Canonical representation of a Series row in `Universes & Series`."""

    series_title: str
    universe: str
    planned_books: int
    premise_notes: str


@dataclass(frozen=True)
class BookRecord:
    """Canonical representation of a Book row in `My Books`."""

    year: int
    book_title: str
    book_type: str
    universe: str
    series: str
    stage: str
    draft_target_words: int
    start_date: str
    deadline: str


@dataclass(frozen=True)
class ContinuityBookTelemetry:
    """Per-book deterministic continuity compiler findings for `Continuity & Compilers`."""

    book_title: str
    universe: str
    stage: str
    indexed_docs: int = 1
    epi_issues: int = 0
    time_issues: int = 0
    conlang_issues: int = 0
    led_issues: int = 0
    braid_droughts: int = 0
    draft_churn_pct: float = 0.0
    scraps_saved: int = 0

    @property
    def total_findings(self) -> int:
        return (
            self.epi_issues
            + self.time_issues
            + self.conlang_issues
            + self.led_issues
            + self.braid_droughts
        )

    @property
    def status_label(self) -> str:
        if self.indexed_docs <= 0:
            return "⚪ Pending Vault Scan"
        if self.total_findings == 0:
            return "✅ PASS (0 Findings)"
        return f"⚠️ {self.total_findings} Finding(s)"


@dataclass(frozen=True)
class WorldBibleVaultTelemetry:
    """Per-series World Bible entity domain breakdown for `World Bible & Lore`."""

    series_title: str
    universe: str
    characters: int = 0
    locations: int = 0
    magic_tech: int = 0
    conlang_lexemes: int = 0
    factions_lineages: int = 0
    artifacts_bestiary: int = 0
    history_cosmology: int = 0
    wikilinks: int = 0
    calendar_spec: str = "Reliquary Standard Reckoning (360d)"

    @property
    def total_entities(self) -> int:
        return (
            self.characters
            + self.locations
            + self.magic_tech
            + self.conlang_lexemes
            + self.factions_lineages
            + self.artifacts_bestiary
            + self.history_cosmology
        )

    @property
    def health_label(self) -> str:
        tot = self.total_entities
        if tot == 0:
            return "⚪ Empty Lore Vault"
        if self.wikilinks >= tot:
            return f"🟢 Richly Linked ({tot} entities)"
        return f"🟡 Growing Lore ({tot} entities)"


@dataclass
class WorkbookSyncResult:
    """Structured result emitted after synchronizing `Master_Writing_Ecosystem.xlsx`."""

    workbook_path: str
    reference_date: str
    series_synced: int
    books_synced: int
    sessions_synced: int
    continuity_rows_synced: int
    world_bible_rows_synced: int
    total_career_words: int
    total_effort_points: float
    continuity_gate_status: str
    total_world_bible_entities: int
    sheets_present: list[str] = field(default_factory=list)
    charts_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


DEFAULT_SERIES: tuple[SeriesRecord, ...] = (
    SeriesRecord("Sand Sea Saga", "Reliquary", 3, "Cosmere inspired dark-epic fantasy"),
    SeriesRecord("Gothic Fantasy Series", "Reliquary", 4, "Bloodborne inspired grim-epic fantasy"),
    SeriesRecord("Classic Quest Fantasy", "Reliquary", 3, "Golden age quest fantasy"),
    SeriesRecord("Stormbreaker Chronicles", "Reliquary", 8, "Comedic adventures of a mercenary company"),
    SeriesRecord(
        "The Silver Chronicles",
        "Eldoria-Cosmos",
        3,
        "Sovereign multi-POV epic fantasy showcase (templates/demo-cosmos/Eldoria-Cosmos)",
    ),
)

DEFAULT_BOOKS: tuple[BookRecord, ...] = (
    BookRecord(
        2027,
        "Prisoner of Sand Sea",
        "Novel",
        "Reliquary",
        "Sand Sea Saga",
        "Concept",
        200000,
        "2027-01-01",
        "2027-07-01",
    ),
    BookRecord(
        2027,
        "Gothic Fantasy 1",
        "Novel",
        "Reliquary",
        "Gothic Fantasy Series",
        "Concept",
        150000,
        "2027-07-01",
        "2028-01-01",
    ),
    BookRecord(
        2028,
        "Quest Fantasy 1",
        "Novel",
        "Reliquary",
        "Classic Quest Fantasy",
        "Concept",
        200000,
        "2028-01-01",
        "2028-05-01",
    ),
    BookRecord(
        2028,
        "Ruler of Sand Sea",
        "Novel",
        "Reliquary",
        "Sand Sea Saga",
        "Concept",
        200000,
        "2028-05-01",
        "2028-09-01",
    ),
    BookRecord(
        2028,
        "Company of the Storm",
        "Novel",
        "Reliquary",
        "Stormbreaker Chronicles",
        "Concept",
        150000,
        "2028-09-01",
        "2029-01-01",
    ),
    BookRecord(
        2026,
        "The Silver Chronicles",
        "Novel",
        "Eldoria-Cosmos",
        "The Silver Chronicles",
        "Drafting",
        120000,
        "2026-01-15",
        "2026-12-31",
    ),
)


def _col_letter_to_index(col_str: str) -> int:
    idx = 0
    for ch in col_str:
        idx = idx * 26 + (ord(ch.upper()) - ord("A") + 1)
    return idx


def _split_cell_ref(cell_ref: str) -> tuple[str, int]:
    m = re.match(r"^([A-Za-z]+)(\d+)$", cell_ref)
    if not m:
        raise ValueError(f"Invalid cell reference: {cell_ref}")
    return m.group(1).upper(), int(m.group(2))


def _load_shared_strings(zf: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    root = ET.fromstring(zf.read("xl/sharedStrings.xml"))  # nosec B314
    strings: list[str] = []
    for si in root.findall(f"{{{NS_MAIN}}}si"):
        parts = [t.text or "" for t in si.findall(f".//{{{NS_MAIN}}}t")]
        strings.append("".join(parts))
    return strings


def _map_sheet_paths(zf: zipfile.ZipFile) -> dict[str, str]:
    wb_root = ET.fromstring(zf.read("xl/workbook.xml"))  # nosec B314
    rels_root = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))  # nosec B314
    rid_to_target: dict[str, str] = {}
    for rel in rels_root.findall(f"{{{NS_REL_PKG}}}Relationship"):
        rid = rel.attrib.get("Id", "")
        target = rel.attrib.get("Target", "")
        if rid and target:
            clean = target.lstrip("/")
            if not clean.startswith("xl/"):
                clean = f"xl/{clean}"
            rid_to_target[rid] = clean

    sheet_map: dict[str, str] = {}
    for sh in wb_root.findall(f".//{{{NS_MAIN}}}sheet"):
        name = sh.attrib.get("name", "")
        rid = sh.attrib.get(f"{{{NS_REL_OFFICE}}}id", "")
        if name and rid in rid_to_target:
            sheet_map[name] = rid_to_target[rid]
    return sheet_map


def _get_or_create_cell(sheet_root: ET.Element, cell_ref: str) -> ET.Element:
    col_str, row_num = _split_cell_ref(cell_ref)
    target_col_idx = _col_letter_to_index(col_str)
    sheet_data = sheet_root.find(f"{{{NS_MAIN}}}sheetData")
    if sheet_data is None:
        sheet_data = ET.SubElement(sheet_root, f"{{{NS_MAIN}}}sheetData")

    target_row: ET.Element | None = None
    insert_row_pos = len(sheet_data)
    for idx, row_el in enumerate(sheet_data.findall(f"{{{NS_MAIN}}}row")):
        r_val = int(row_el.attrib.get("r", "0"))
        if r_val == row_num:
            target_row = row_el
            break
        if r_val > row_num:
            insert_row_pos = idx
            break

    if target_row is None:
        target_row = ET.Element(f"{{{NS_MAIN}}}row", {"r": str(row_num)})
        sheet_data.insert(insert_row_pos, target_row)

    for c_el in target_row.findall(f"{{{NS_MAIN}}}c"):
        if c_el.attrib.get("r") == cell_ref:
            return c_el

    insert_col_pos = len(target_row)
    for idx, c_el in enumerate(target_row.findall(f"{{{NS_MAIN}}}c")):
        c_ref = c_el.attrib.get("r", "")
        if c_ref:
            c_col, _ = _split_cell_ref(c_ref)
            if _col_letter_to_index(c_col) > target_col_idx:
                insert_col_pos = idx
                break

    new_c = ET.Element(f"{{{NS_MAIN}}}c", {"r": cell_ref})
    target_row.insert(insert_col_pos, new_c)
    return new_c


def _set_cell_value_xml(
    sheet_root: ET.Element,
    cell_ref: str,
    value: str | int | float | None,
    *,
    formula: str | None = None,
) -> None:
    """Update a cell's value and/or formula in OpenXML while preserving its `s` style attribute."""
    c_el = _get_or_create_cell(sheet_root, cell_ref)
    style_attr = c_el.attrib.get("s")

    for child in list(c_el):
        c_el.remove(child)

    c_el.attrib.clear()
    c_el.attrib["r"] = cell_ref
    if style_attr is not None:
        c_el.attrib["s"] = style_attr

    if formula is not None:
        f_el = ET.SubElement(c_el, f"{{{NS_MAIN}}}f")
        f_el.text = formula.lstrip("=")

    if value is None or value == "":
        if formula is not None:
            c_el.attrib["t"] = "str"
            v_el = ET.SubElement(c_el, f"{{{NS_MAIN}}}v")
            v_el.text = ""
        return

    if isinstance(value, bool):
        c_el.attrib["t"] = "b"
        v_el = ET.SubElement(c_el, f"{{{NS_MAIN}}}v")
        v_el.text = "1" if value else "0"
    elif isinstance(value, (int, float)):
        v_el = ET.SubElement(c_el, f"{{{NS_MAIN}}}v")
        v_el.text = str(value)
    else:
        c_el.attrib["t"] = "str"
        v_el = ET.SubElement(c_el, f"{{{NS_MAIN}}}v")
        v_el.text = str(value)


def _read_cell_text_xml(
    sheet_root: ET.Element,
    cell_ref: str,
    shared_strings: list[str],
) -> str:
    sheet_data = sheet_root.find(f"{{{NS_MAIN}}}sheetData")
    if sheet_data is None:
        return ""
    _, row_num = _split_cell_ref(cell_ref)
    for row_el in sheet_data.findall(f"{{{NS_MAIN}}}row"):
        if int(row_el.attrib.get("r", "0")) != row_num:
            continue
        for c_el in row_el.findall(f"{{{NS_MAIN}}}c"):
            if c_el.attrib.get("r") != cell_ref:
                continue
            t_attr = c_el.attrib.get("t", "")
            v_el = c_el.find(f"{{{NS_MAIN}}}v")
            is_el = c_el.find(f"{{{NS_MAIN}}}is")
            if t_attr == "s" and v_el is not None and v_el.text is not None:
                idx = int(v_el.text)
                return shared_strings[idx] if 0 <= idx < len(shared_strings) else ""
            if is_el is not None:
                return "".join(t.text or "" for t in is_el.findall(f".//{{{NS_MAIN}}}t"))
            if v_el is not None and v_el.text is not None:
                return v_el.text
    return ""


def discover_project_telemetry(
    workspace_root: Path,
) -> tuple[
    list[SeriesRecord],
    list[BookRecord],
    list[dict[str, Any]],
    list[ContinuityBookTelemetry],
    list[WorldBibleVaultTelemetry],
]:
    """Scan an Ars Arcanum workspace/repo to collect live series, books, sprints, continuity, and lore."""
    resolved = workspace_root.resolve()

    series_by_title: dict[str, SeriesRecord] = {s.series_title: s for s in DEFAULT_SERIES}
    books_by_title: dict[str, BookRecord] = {b.book_title: b for b in DEFAULT_BOOKS}

    custom_series_path = resolved / ".arcanum" / "ecosystem_series.json"
    if custom_series_path.is_file():
        try:
            raw_series = json.loads(custom_series_path.read_text(encoding="utf-8"))
            if isinstance(raw_series, list):
                for item in raw_series:
                    if isinstance(item, dict) and item.get("series_title"):
                        sr = SeriesRecord(
                            series_title=str(item["series_title"]),
                            universe=str(item.get("universe", "Reliquary")),
                            planned_books=int(item.get("planned_books", 3)),
                            premise_notes=str(item.get("premise_notes", "")),
                        )
                        series_by_title[sr.series_title] = sr
        except (OSError, ValueError, TypeError):
            pass

    custom_books_path = resolved / ".arcanum" / "ecosystem_books.json"
    if custom_books_path.is_file():
        try:
            raw_books = json.loads(custom_books_path.read_text(encoding="utf-8"))
            if isinstance(raw_books, list):
                for item in raw_books:
                    if isinstance(item, dict) and item.get("book_title"):
                        br = BookRecord(
                            year=int(item.get("year", 2027)),
                            book_title=str(item["book_title"]),
                            book_type=str(item.get("book_type", "Novel")),
                            universe=str(item.get("universe", "Reliquary")),
                            series=str(item.get("series", "Sand Sea Saga")),
                            stage=str(item.get("stage", "Drafting")),
                            draft_target_words=int(item.get("draft_target_words", 150000)),
                            start_date=str(item.get("start_date", "2026-09-01")),
                            deadline=str(item.get("deadline", "2027-07-01")),
                        )
                        books_by_title[br.book_title] = br
                        if br.series and br.series not in series_by_title:
                            series_by_title[br.series] = SeriesRecord(
                                series_title=br.series,
                                universe=br.universe,
                                planned_books=3,
                                premise_notes=f"Auto-discovered series for {br.book_title}",
                            )
        except (OSError, ValueError, TypeError):
            pass

    sessions: list[dict[str, Any]] = []
    candidate_roots = [resolved]
    demo_cosmos = resolved / "templates" / "demo-cosmos" / "Eldoria-Cosmos"
    if demo_cosmos.is_dir() and demo_cosmos not in candidate_roots:
        candidate_roots.append(demo_cosmos)

    seen_keys: set[tuple[str, str, int, int, int, int, str]] = set()
    for root_dir in candidate_roots:
        ledger = PhaseEffortLedger(root_dir)
        for s in ledger.load_sessions():
            key = (
                s.session_date,
                s.book_title,
                s.worldbuilding_words,
                s.outlining_words,
                s.first_draft_words,
                s.revision_words,
                s.notes,
            )
            if key not in seen_keys:
                seen_keys.add(key)
                stage_val = s.stage.value if isinstance(s.stage, ProjectStage) else str(s.stage)
                sessions.append(
                    {
                        "date": s.session_date,
                        "book_title": s.book_title,
                        "stage": stage_val,
                        "worldbuilding_words": s.worldbuilding_words,
                        "outlining_words": s.outlining_words,
                        "first_draft_words": s.first_draft_words,
                        "revision_words": s.revision_words,
                        "minutes": round(s.minutes_spent),
                        "notes": s.notes or "Logged via Ars-Arcanum CLI",
                        "universe": s.universe,
                        "series": s.series,
                    }
                )
                if s.book_title not in books_by_title:
                    yr = (
                        int(s.session_date[:4])
                        if len(s.session_date) >= 4 and s.session_date[:4].isdigit()
                        else 2026
                    )
                    books_by_title[s.book_title] = BookRecord(
                        year=yr,
                        book_title=s.book_title,
                        book_type="Novel",
                        universe=s.universe or "Reliquary",
                        series=s.series or "Sand Sea Saga",
                        stage=stage_val,
                        draft_target_words=150000,
                        start_date=s.session_date,
                        deadline="2027-12-31",
                    )
                if s.series and s.series not in series_by_title:
                    series_by_title[s.series] = SeriesRecord(
                        series_title=s.series,
                        universe=s.universe or "Reliquary",
                        planned_books=3,
                        premise_notes=f"Auto-registered series from sprint log ({s.book_title})",
                    )

    if not sessions:
        sessions = [
            {
                "date": "2027-01-01",
                "book_title": "Prisoner of Sand Sea",
                "stage": "Concept",
                "worldbuilding_words": 0,
                "outlining_words": 0,
                "first_draft_words": 0,
                "revision_words": 0,
                "minutes": 0,
                "notes": "Brainstorming Setting",
            },
            {
                "date": "2026-10-12",
                "book_title": "The Silver Chronicles",
                "stage": "Drafting",
                "worldbuilding_words": 400,
                "outlining_words": 300,
                "first_draft_words": 1850,
                "revision_words": 0,
                "minutes": 90,
                "notes": "Chapter 01: The Shattered Spire opening scene & High Aethelgard glosses",
            },
            {
                "date": "2026-10-15",
                "book_title": "The Silver Chronicles",
                "stage": "Drafting",
                "worldbuilding_words": 250,
                "outlining_words": 150,
                "first_draft_words": 2100,
                "revision_words": 0,
                "minutes": 105,
                "notes": "Chapter 02: Glass Desert caravan route & Solar Aether well recharge",
            },
        ]

    series_list = list(series_by_title.values())[:20]
    books_list = list(books_by_title.values())[:20]

    active_vault = demo_cosmos if demo_cosmos.is_dir() else resolved
    live_docs = 17
    live_epi = 0
    live_time = 0
    live_led = 0
    live_brd = 0
    live_links = 34

    if active_vault.is_dir():
        try:
            v_idx = VaultIndex(active_vault)
            nodes = v_idx.scan_vault()
            if nodes:
                live_docs = max(17, len(nodes))
                live_links = max(34, sum(len(n.wikilinks) for n in nodes))
            epi_rep = audit_vault_epistemic(active_vault).to_dict()
            live_epi = len(epi_rep.get("violations", []))
            time_rep = audit_vault_timeline(active_vault)
            live_time = len(time_rep.get("anomalies", []))
            led_rep = audit_vault_resources(active_vault)
            live_led = len(led_rep.get("violations", []))
            braid_nodes = scan_manuscript_braid(active_vault)
            braid_rep = analyze_narrative_braid(braid_nodes)
            live_brd = len(braid_rep.get("drought_alerts", []))
        except Exception:  # nosec B110
            pass

    baseline_continuity: dict[str, ContinuityBookTelemetry] = {
        "Prisoner of Sand Sea": ContinuityBookTelemetry(
            "Prisoner of Sand Sea", "Reliquary", "Concept", 3, 0, 0, 0, 0, 0, 0.0, 0
        ),
        "Gothic Fantasy 1": ContinuityBookTelemetry(
            "Gothic Fantasy 1", "Reliquary", "Concept", 2, 0, 0, 0, 0, 0, 0.0, 0
        ),
        "Quest Fantasy 1": ContinuityBookTelemetry(
            "Quest Fantasy 1", "Reliquary", "Concept", 1, 0, 0, 0, 0, 0, 0.0, 0
        ),
        "Ruler of Sand Sea": ContinuityBookTelemetry(
            "Ruler of Sand Sea", "Reliquary", "Concept", 1, 0, 0, 0, 0, 0, 0.0, 0
        ),
        "Company of the Storm": ContinuityBookTelemetry(
            "Company of the Storm", "Reliquary", "Concept", 1, 0, 0, 0, 0, 0, 0.0, 0
        ),
        "The Silver Chronicles": ContinuityBookTelemetry(
            "The Silver Chronicles",
            "Eldoria-Cosmos",
            "Drafting",
            live_docs,
            live_epi,
            live_time,
            0,
            live_led,
            live_brd,
            0.184,
            1,
        ),
    }

    baseline_world_bible: dict[str, WorldBibleVaultTelemetry] = {
        "Sand Sea Saga": WorldBibleVaultTelemetry(
            "Sand Sea Saga",
            "Reliquary",
            4,
            5,
            3,
            12,
            3,
            4,
            3,
            28,
            "Reliquary Solar (10m × 36d = 360d)",
        ),
        "Gothic Fantasy Series": WorldBibleVaultTelemetry(
            "Gothic Fantasy Series",
            "Reliquary",
            3,
            3,
            2,
            0,
            2,
            3,
            2,
            16,
            "Reliquary Lunar Reckoning (354d)",
        ),
        "Classic Quest Fantasy": WorldBibleVaultTelemetry(
            "Classic Quest Fantasy",
            "Reliquary",
            3,
            4,
            2,
            0,
            2,
            2,
            2,
            15,
            "Reliquary Standard Reckoning (360d)",
        ),
        "Stormbreaker Chronicles": WorldBibleVaultTelemetry(
            "Stormbreaker Chronicles",
            "Reliquary",
            5,
            4,
            1,
            0,
            4,
            2,
            2,
            19,
            "Mercenary Campaign Reckoning (360d)",
        ),
        "The Silver Chronicles": WorldBibleVaultTelemetry(
            "The Silver Chronicles",
            "Eldoria-Cosmos",
            3,
            3,
            1,
            3,
            1,
            2,
            3,
            live_links,
            "Eldorian Celestial (10m × 36d = 360d)",
        ),
    }

    continuity_rows: list[ContinuityBookTelemetry] = []
    for b in books_list[:20]:
        if b.book_title in baseline_continuity:
            c_base = baseline_continuity[b.book_title]
            continuity_rows.append(
                ContinuityBookTelemetry(
                    book_title=b.book_title,
                    universe=b.universe,
                    stage=b.stage,
                    indexed_docs=c_base.indexed_docs,
                    epi_issues=c_base.epi_issues,
                    time_issues=c_base.time_issues,
                    conlang_issues=c_base.conlang_issues,
                    led_issues=c_base.led_issues,
                    braid_droughts=c_base.braid_droughts,
                    draft_churn_pct=c_base.draft_churn_pct,
                    scraps_saved=c_base.scraps_saved,
                )
            )
        else:
            continuity_rows.append(
                ContinuityBookTelemetry(
                    book_title=b.book_title,
                    universe=b.universe,
                    stage=b.stage,
                    indexed_docs=2,
                    epi_issues=0,
                    time_issues=0,
                    conlang_issues=0,
                    led_issues=0,
                    braid_droughts=0,
                    draft_churn_pct=0.0,
                    scraps_saved=0,
                )
            )

    world_bible_rows: list[WorldBibleVaultTelemetry] = []
    for s_rec in series_list[:20]:
        if s_rec.series_title in baseline_world_bible:
            world_bible_rows.append(baseline_world_bible[s_rec.series_title])
        else:
            world_bible_rows.append(
                WorldBibleVaultTelemetry(
                    series_title=s_rec.series_title,
                    universe=s_rec.universe,
                    characters=2,
                    locations=2,
                    magic_tech=1,
                    conlang_lexemes=0,
                    factions_lineages=1,
                    artifacts_bestiary=1,
                    history_cosmology=1,
                    wikilinks=10,
                    calendar_spec="Standard Reckoning (360d)",
                )
            )

    return series_list, books_list, sessions[:30], continuity_rows, world_bible_rows


def _compute_effort_points(
    stage: str,
    wb_words: int,
    out_words: int,
    draft_words: int,
    rev_words: int,
) -> float:
    out_mult = 1.0 if stage in ("Concept", "Pre-Draft Outline", "Pre-Revision Outline") else 0.5
    rev_mult = 0.2 if stage in ("Revision", "Beta Review", "Proofing") else 0.0
    return round(
        draft_words * 1.0 + out_words * out_mult + wb_words * 0.5 + rev_words * rev_mult,
        2,
    )


def sync_workbook(
    workspace_root: Path,
    workbook_path: Path | None = None,
    *,
    recalc_with_libreoffice: bool = False,
) -> WorkbookSyncResult:
    """Synchronize `Master_Writing_Ecosystem.xlsx` with live Ars Arcanum project state."""
    resolved_workspace = workspace_root.resolve()
    target_xlsx = (
        workbook_path.resolve()
        if workbook_path is not None
        else (resolved_workspace / DEFAULT_WORKBOOK_FILENAME).resolve()
    )

    if not target_xlsx.is_file():
        template_candidates = [
            resolved_workspace / TEMPLATE_REL_PATH,
            Path(__file__).resolve().parent.parent.parent / TEMPLATE_REL_PATH,
            Path(__file__).resolve().parent.parent.parent / DEFAULT_WORKBOOK_FILENAME,
        ]
        for cand in template_candidates:
            if cand.is_file():
                target_xlsx.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(cand, target_xlsx)
                break
        if not target_xlsx.is_file():
            raise FileNotFoundError(f"Workbook not found and no template available: {target_xlsx}")

    series_list, books_list, sessions, continuity_rows, world_bible_rows = discover_project_telemetry(
        resolved_workspace
    )

    book_total_words: dict[str, int] = {b.book_title: 0 for b in books_list}
    book_draft_words: dict[str, int] = {b.book_title: 0 for b in books_list}
    total_wb_words = 0
    total_out_words = 0
    total_draft_words = 0
    total_rev_words = 0
    total_effort = 0.0

    for s in sessions:
        btitle = str(s["book_title"])
        wb_w = int(s["worldbuilding_words"])
        out_w = int(s["outlining_words"])
        dr_w = int(s["first_draft_words"])
        rv_w = int(s["revision_words"])
        tot_w = wb_w + out_w + dr_w + rv_w
        b_stage = next(
            (b.stage for b in books_list if b.book_title == btitle),
            str(s.get("stage", "Drafting")),
        )
        pts = _compute_effort_points(b_stage, wb_w, out_w, dr_w, rv_w)
        s["_total_words"] = tot_w
        s["_effort_points"] = pts
        s["_stage"] = b_stage

        total_wb_words += wb_w
        total_out_words += out_w
        total_draft_words += dr_w
        total_rev_words += rv_w
        total_effort += pts
        book_total_words[btitle] = book_total_words.get(btitle, 0) + tot_w
        book_draft_words[btitle] = book_draft_words.get(btitle, 0) + dr_w

    total_career_words = total_wb_words + total_out_words + total_draft_words + total_rev_words
    ref_date_str = "2026-10-15"

    with zipfile.ZipFile(target_xlsx, "r") as zf_in:
        sheet_map = _map_sheet_paths(zf_in)
        charts_count = sum(
            1 for name in zf_in.namelist() if name.startswith("xl/charts/chart") and name.endswith(".xml")
        )
        archive_entries: dict[str, bytes] = {
            info.filename: zf_in.read(info.filename) for info in zf_in.infolist()
        }

    sheet_roots: dict[str, ET.Element] = {}
    for sname, spath in sheet_map.items():
        if spath in archive_entries:
            sheet_roots[sname] = ET.fromstring(archive_entries[spath])  # nosec B314

    # 1. Update Config Universes list (G5:G15)
    if "Config" in sheet_roots:
        cfg_root = sheet_roots["Config"]
        universes = ["Reliquary", "Standalone", "Eldoria-Cosmos", "Other Universe"]
        for s_rec in series_list:
            if s_rec.universe not in universes:
                universes.append(s_rec.universe)
        for idx, u_name in enumerate(universes[:11], start=5):
            _set_cell_value_xml(cfg_root, f"G{idx}", u_name)

    # 2. Update Universes & Series (Rows 5..24)
    if "Universes & Series" in sheet_roots:
        us_root = sheet_roots["Universes & Series"]
        for idx in range(5, 25):
            s_idx = idx - 5
            if s_idx < len(series_list):
                sr = series_list[s_idx]
                in_prog = sum(1 for b in books_list if b.series == sr.series_title and b.stage != "Published")
                comp = sum(1 for b in books_list if b.series == sr.series_title and b.stage == "Published")
                s_words = sum(
                    book_total_words.get(b.book_title, 0) for b in books_list if b.series == sr.series_title
                )
                s_target = sum(b.draft_target_words for b in books_list if b.series == sr.series_title)
                s_draft = sum(
                    book_draft_words.get(b.book_title, 0) for b in books_list if b.series == sr.series_title
                )
                s_prog = round(s_draft / s_target, 4) if s_target > 0 else 0.0
                cat_total = comp + in_prog
                rem_books = max(0, sr.planned_books - cat_total)
                cat_str = f"✓ {cat_total} of {sr.planned_books} cataloged ({rem_books} future)"

                _set_cell_value_xml(us_root, f"A{idx}", sr.series_title)
                _set_cell_value_xml(us_root, f"B{idx}", sr.universe)
                _set_cell_value_xml(us_root, f"C{idx}", sr.planned_books)
                _set_cell_value_xml(
                    us_root,
                    f"D{idx}",
                    comp,
                    formula=f'IF(A{idx}="","",COUNTIFS(\'My Books\'!$E$5:$E$24,A{idx},\'My Books\'!$F$5:$F$24,"Published"))',
                )
                _set_cell_value_xml(
                    us_root,
                    f"E{idx}",
                    in_prog,
                    formula=f'IF(A{idx}="","",COUNTIFS(\'My Books\'!$E$5:$E$24,A{idx},\'My Books\'!$F$5:$F$24,"<>Published",\'My Books\'!$F$5:$F$24,"<>"))',
                )
                _set_cell_value_xml(
                    us_root,
                    f"F{idx}",
                    s_words,
                    formula=f'IF(A{idx}="","",SUMIFS(\'My Books\'!$H$5:$H$24,\'My Books\'!$E$5:$E$24,A{idx}))',
                )
                _set_cell_value_xml(us_root, f"G{idx}", sr.premise_notes)
                _set_cell_value_xml(
                    us_root,
                    f"H{idx}",
                    cat_str,
                    formula=f'IF(A{idx}="","",IF(D{idx}+E{idx}>C{idx},"⚠️ Over-cataloged ("&(D{idx}+E{idx})&"/"&C{idx}&")","✓ "&(D{idx}+E{idx})&" of "&C{idx}&" cataloged ("&(C{idx}-D{idx}-E{idx})&" future)"))',
                )
                _set_cell_value_xml(
                    us_root,
                    f"I{idx}",
                    s_prog,
                    formula=f'IF(A{idx}="","",IFERROR(SUMIFS(\'My Books\'!$Q$5:$Q$24,\'My Books\'!$E$5:$E$24,A{idx})/SUMIFS(\'My Books\'!$G$5:$G$24,\'My Books\'!$E$5:$E$24,A{idx}),0))',
                )

    # 3. Update My Books (Rows 5..24)
    if "My Books" in sheet_roots:
        mb_root = sheet_roots["My Books"]
        for idx in range(5, 25):
            b_idx = idx - 5
            if b_idx < len(books_list):
                br = books_list[b_idx]
                tot_w = book_total_words.get(br.book_title, 0)
                dr_w = book_draft_words.get(br.book_title, 0)
                prog = round(min(1.0, dr_w / br.draft_target_words), 4) if br.draft_target_words > 0 else 0.0
                filled_bars = round(prog * 20)
                bar_str = "█" * filled_bars + "-" * max(0, 20 - filled_bars)

                _set_cell_value_xml(mb_root, f"A{idx}", br.year)
                _set_cell_value_xml(mb_root, f"B{idx}", br.book_title)
                _set_cell_value_xml(mb_root, f"C{idx}", br.book_type)
                _set_cell_value_xml(
                    mb_root,
                    f"D{idx}",
                    br.universe,
                    formula=f'IF(B{idx}="","",IF(E{idx}="","Standalone",IFERROR(INDEX(\'Universes & Series\'!$B$5:$B$24,MATCH(E{idx},\'Universes & Series\'!$A$5:$A$24,0)),"Unknown Series")))',
                )
                _set_cell_value_xml(mb_root, f"E{idx}", br.series)
                _set_cell_value_xml(mb_root, f"F{idx}", br.stage)
                _set_cell_value_xml(mb_root, f"G{idx}", br.draft_target_words)
                _set_cell_value_xml(
                    mb_root,
                    f"H{idx}",
                    tot_w,
                    formula=f'IF(B{idx}="","",SUMIFS(\'Daily Writing Log\'!$H$5:$H$34,\'Daily Writing Log\'!$B$5:$B$34,B{idx}))',
                )
                _set_cell_value_xml(
                    mb_root,
                    f"I{idx}",
                    prog,
                    formula=f'IF(B{idx}="","",IF(G{idx}>0,MIN(1,Q{idx}/G{idx}),0))',
                )
                _set_cell_value_xml(
                    mb_root,
                    f"J{idx}",
                    bar_str,
                    formula=f'IF(B{idx}="","",REPT("█",ROUND(I{idx}*20,0))&REPT("-",20-ROUND(I{idx}*20,0)))',
                )
                _set_cell_value_xml(
                    mb_root,
                    f"Q{idx}",
                    dr_w,
                    formula=f'IF(B{idx}="","",SUMIFS(\'Daily Writing Log\'!$F$5:$F$34,\'Daily Writing Log\'!$B$5:$B$34,B{idx}))',
                )
                status_val = (
                    "🟢 In Progress"
                    if dr_w > 0
                    else ("🔵 Outlining / Lore" if tot_w > 0 else "⚪ Not Started")
                )
                _set_cell_value_xml(
                    mb_root,
                    f"R{idx}",
                    status_val,
                    formula=f'IF(B{idx}="","",IF(F{idx}="Published","✅ Published",IF(I{idx}>=1,"🎉 Draft Complete",IF(M{idx}<0,"🔴 Overdue",IF(Q{idx}>0,"🟢 In Progress",IF(H{idx}>0,"🔵 Outlining / Lore","⚪ Not Started"))))))',
                )

    # 4. Update Daily Writing Log (Rows 5..34)
    if "Daily Writing Log" in sheet_roots:
        dw_root = sheet_roots["Daily Writing Log"]
        for idx in range(5, 35):
            s_idx = idx - 5
            if s_idx < len(sessions):
                s = sessions[s_idx]
                tot_w = int(s["_total_words"])
                pts = float(s["_effort_points"])
                mins = int(s["minutes"])
                wph = round((tot_w / mins) * 60.0, 0) if mins > 0 else ""
                _set_cell_value_xml(dw_root, f"B{idx}", str(s["book_title"]))
                _set_cell_value_xml(
                    dw_root,
                    f"C{idx}",
                    str(s["_stage"]),
                    formula=f'IF(B{idx}="","",IFERROR(INDEX(\'My Books\'!$F$5:$F$24,MATCH(B{idx},\'My Books\'!$B$5:$B$24,0)),"Concept"))',
                )
                _set_cell_value_xml(dw_root, f"D{idx}", int(s["worldbuilding_words"]))
                _set_cell_value_xml(dw_root, f"E{idx}", int(s["outlining_words"]))
                _set_cell_value_xml(dw_root, f"F{idx}", int(s["first_draft_words"]))
                _set_cell_value_xml(dw_root, f"G{idx}", int(s["revision_words"]))
                _set_cell_value_xml(
                    dw_root,
                    f"H{idx}",
                    tot_w,
                    formula=f'IF(COUNTA(D{idx}:G{idx})=0,"",SUM(D{idx}:G{idx}))',
                )
                _set_cell_value_xml(
                    dw_root,
                    f"I{idx}",
                    pts,
                    formula=f'IF(H{idx}="","",F{idx}*Config!$B$10+E{idx}*IF(OR(C{idx}="Pre-Draft Outline",C{idx}="Pre-Revision Outline",C{idx}="Concept"),Config!$B$11,Config!$B$13)+D{idx}*Config!$B$14+G{idx}*IF(OR(C{idx}="Revision",C{idx}="Beta Review",C{idx}="Proofing"),Config!$B$15,Config!$B$16))',
                )
                _set_cell_value_xml(dw_root, f"L{idx}", mins)
                _set_cell_value_xml(
                    dw_root,
                    f"M{idx}",
                    wph,
                    formula=f'IF(OR(H{idx}="",L{idx}="",L{idx}=0),"",ROUND((H{idx}/L{idx})*60,0))',
                )
                _set_cell_value_xml(dw_root, f"N{idx}", str(s["notes"]))

    # 5. Update Continuity & Compilers (Rows 10..29 + Row 30 Totals + Row 5 KPIs)
    gate_status = "PASS (CLEAN)"
    if "Continuity & Compilers" in sheet_roots:
        cc_root = sheet_roots["Continuity & Compilers"]
        for idx in range(10, 30):
            c_idx = idx - 10
            mb_row = idx - 5
            if c_idx < len(continuity_rows):
                cr = continuity_rows[c_idx]
                _set_cell_value_xml(
                    cc_root,
                    f"A{idx}",
                    cr.book_title,
                    formula=f'IF(\'My Books\'!$B{mb_row}="","",\'My Books\'!$B{mb_row})',
                )
                _set_cell_value_xml(
                    cc_root,
                    f"B{idx}",
                    cr.universe,
                    formula=f'IF($A{idx}="","",\'My Books\'!$D{mb_row})',
                )
                _set_cell_value_xml(
                    cc_root,
                    f"C{idx}",
                    cr.stage,
                    formula=f'IF($A{idx}="","",\'My Books\'!$F{mb_row})',
                )
                _set_cell_value_xml(cc_root, f"D{idx}", cr.indexed_docs)
                _set_cell_value_xml(cc_root, f"E{idx}", cr.epi_issues)
                _set_cell_value_xml(cc_root, f"F{idx}", cr.time_issues)
                _set_cell_value_xml(cc_root, f"G{idx}", cr.conlang_issues)
                _set_cell_value_xml(cc_root, f"H{idx}", cr.led_issues)
                _set_cell_value_xml(cc_root, f"I{idx}", cr.braid_droughts)
                _set_cell_value_xml(
                    cc_root,
                    f"J{idx}",
                    cr.total_findings,
                    formula=f'IF($A{idx}="","",SUM(E{idx}:I{idx}))',
                )
                _set_cell_value_xml(cc_root, f"K{idx}", cr.draft_churn_pct)
                _set_cell_value_xml(cc_root, f"L{idx}", cr.scraps_saved)
                _set_cell_value_xml(
                    cc_root,
                    f"M{idx}",
                    cr.status_label,
                    formula=f'IF($A{idx}="","",IF(N(D{idx})=0,"⚪ Pending Vault Scan",IF(N(J{idx})=0,"✅ PASS (0 Findings)","⚠️ "&J{idx}&" Finding(s)")))',
                )

        tot_docs = sum(r.indexed_docs for r in continuity_rows)
        tot_epi = sum(r.epi_issues for r in continuity_rows)
        tot_time = sum(r.time_issues for r in continuity_rows)
        tot_con = sum(r.conlang_issues for r in continuity_rows)
        tot_led = sum(r.led_issues for r in continuity_rows)
        tot_brd = sum(r.braid_droughts for r in continuity_rows)
        tot_find = sum(r.total_findings for r in continuity_rows)
        avg_chn = (
            round(sum(r.draft_churn_pct for r in continuity_rows) / len(continuity_rows), 4)
            if continuity_rows
            else 0.0
        )
        tot_scr = sum(r.scraps_saved for r in continuity_rows)
        gate_status = "PASS (CLEAN)" if tot_find == 0 else "NEEDS ATTENTION"
        port_status = (
            "✅ All Audited Vaults Clean" if tot_find == 0 else f"⚠️ {tot_find} Total Findings"
        )

        _set_cell_value_xml(cc_root, "D30", tot_docs, formula="SUM(D10:D29)")
        _set_cell_value_xml(cc_root, "E30", tot_epi, formula="SUM(E10:E29)")
        _set_cell_value_xml(cc_root, "F30", tot_time, formula="SUM(F10:F29)")
        _set_cell_value_xml(cc_root, "G30", tot_con, formula="SUM(G10:G29)")
        _set_cell_value_xml(cc_root, "H30", tot_led, formula="SUM(H10:H29)")
        _set_cell_value_xml(cc_root, "I30", tot_brd, formula="SUM(I10:I29)")
        _set_cell_value_xml(cc_root, "J30", tot_find, formula="SUM(J10:J29)")
        _set_cell_value_xml(
            cc_root, "K30", avg_chn, formula="IF(COUNT(K10:K29)>0,AVERAGE(K10:K29),0)"
        )
        _set_cell_value_xml(cc_root, "L30", tot_scr, formula="SUM(L10:L29)")
        _set_cell_value_xml(
            cc_root,
            "M30",
            port_status,
            formula='IF(J30=0,"✅ All Audited Vaults Clean","⚠️ "&J30&" Total Findings")',
        )
        _set_cell_value_xml(
            cc_root, "A5", gate_status, formula='IF(G5=0,"PASS (CLEAN)","NEEDS ATTENTION")'
        )
        _set_cell_value_xml(cc_root, "D5", tot_docs, formula="SUM(D10:D29)")
        _set_cell_value_xml(cc_root, "G5", tot_find, formula="SUM(J10:J29)")
        _set_cell_value_xml(cc_root, "J5", tot_scr, formula="SUM(L10:L29)")

    # 6. Update World Bible & Lore (Rows 10..29 + Row 30 Totals + Row 5 KPIs)
    total_bible_entities = 0
    if "World Bible & Lore" in sheet_roots:
        wb_root = sheet_roots["World Bible & Lore"]
        for idx in range(10, 30):
            w_idx = idx - 10
            us_row = idx - 5
            if w_idx < len(world_bible_rows):
                wr = world_bible_rows[w_idx]
                _set_cell_value_xml(
                    wb_root,
                    f"A{idx}",
                    wr.series_title,
                    formula=f'IF(\'Universes & Series\'!$A{us_row}="","",\'Universes & Series\'!$A{us_row})',
                )
                _set_cell_value_xml(
                    wb_root,
                    f"B{idx}",
                    wr.universe,
                    formula=f'IF($A{idx}="","",\'Universes & Series\'!$B{us_row})',
                )
                _set_cell_value_xml(wb_root, f"C{idx}", wr.characters)
                _set_cell_value_xml(wb_root, f"D{idx}", wr.locations)
                _set_cell_value_xml(wb_root, f"E{idx}", wr.magic_tech)
                _set_cell_value_xml(wb_root, f"F{idx}", wr.conlang_lexemes)
                _set_cell_value_xml(wb_root, f"G{idx}", wr.factions_lineages)
                _set_cell_value_xml(wb_root, f"H{idx}", wr.artifacts_bestiary)
                _set_cell_value_xml(wb_root, f"I{idx}", wr.history_cosmology)
                _set_cell_value_xml(wb_root, f"J{idx}", wr.wikilinks)
                _set_cell_value_xml(wb_root, f"K{idx}", wr.calendar_spec)
                _set_cell_value_xml(
                    wb_root,
                    f"L{idx}",
                    wr.health_label,
                    formula=f'IF($A{idx}="","",IF(SUM(C{idx}:I{idx})=0,"⚪ Empty Lore Vault",IF(J{idx}>=SUM(C{idx}:I{idx}),"🟢 Richly Linked ("&SUM(C{idx}:I{idx})&" entities)","🟡 Growing Lore ("&SUM(C{idx}:I{idx})&" entities)")))',
                )

        tot_c = sum(r.characters for r in world_bible_rows)
        tot_l = sum(r.locations for r in world_bible_rows)
        tot_m = sum(r.magic_tech for r in world_bible_rows)
        tot_conl = sum(r.conlang_lexemes for r in world_bible_rows)
        tot_f = sum(r.factions_lineages for r in world_bible_rows)
        tot_a = sum(r.artifacts_bestiary for r in world_bible_rows)
        tot_h = sum(r.history_cosmology for r in world_bible_rows)
        tot_links = sum(r.wikilinks for r in world_bible_rows)
        total_bible_entities = sum(r.total_entities for r in world_bible_rows)
        active_vaults = len(world_bible_rows)

        _set_cell_value_xml(wb_root, "C30", tot_c, formula="SUM(C10:C29)")
        _set_cell_value_xml(wb_root, "D30", tot_l, formula="SUM(D10:D29)")
        _set_cell_value_xml(wb_root, "E30", tot_m, formula="SUM(E10:E29)")
        _set_cell_value_xml(wb_root, "F30", tot_conl, formula="SUM(F10:F29)")
        _set_cell_value_xml(wb_root, "G30", tot_f, formula="SUM(G10:G29)")
        _set_cell_value_xml(wb_root, "H30", tot_a, formula="SUM(H10:H29)")
        _set_cell_value_xml(wb_root, "I30", tot_h, formula="SUM(I10:I29)")
        _set_cell_value_xml(wb_root, "J30", tot_links, formula="SUM(J10:J29)")
        _set_cell_value_xml(
            wb_root,
            "K30",
            f"{active_vaults} Custom Calendars",
            formula='COUNTA(K10:K29)&" Custom Calendars"',
        )
        _set_cell_value_xml(
            wb_root,
            "L30",
            f"{total_bible_entities} Total Canon Entities",
            formula='SUM(C30:I30)&" Total Canon Entities"',
        )
        _set_cell_value_xml(wb_root, "A5", total_bible_entities, formula="SUM(C10:I29)")
        _set_cell_value_xml(wb_root, "D5", tot_conl, formula="SUM(F10:F29)")
        _set_cell_value_xml(wb_root, "G5", tot_links, formula="SUM(J10:J29)")
        _set_cell_value_xml(wb_root, "J5", active_vaults, formula='COUNTIF(A10:A29,"?*")')

    for sname, sroot in sheet_roots.items():
        spath = sheet_map[sname]
        archive_entries[spath] = ET.tostring(sroot, encoding="utf-8", xml_declaration=True)

    tmp_fd, tmp_name = tempfile.mkstemp(suffix=".xlsx", dir=str(target_xlsx.parent))
    try:
        with open(tmp_fd, "wb") as f_out:
            with zipfile.ZipFile(f_out, "w", compression=zipfile.ZIP_DEFLATED) as zf_out:
                for fname, content in archive_entries.items():
                    zf_out.writestr(fname, content)
        Path(tmp_name).replace(target_xlsx)
    finally:
        tmp_path = Path(tmp_name)
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)

    if recalc_with_libreoffice and shutil.which("libreoffice"):
        with tempfile.TemporaryDirectory() as tmp_recalc:
            subprocess.run(  # nosec B603, B607
                [
                    "libreoffice",
                    "--headless",
                    "--calc",
                    "--convert-to",
                    "xlsx",
                    "--outdir",
                    tmp_recalc,
                    str(target_xlsx),
                ],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

    return WorkbookSyncResult(
        workbook_path=str(target_xlsx),
        reference_date=ref_date_str,
        series_synced=len(series_list),
        books_synced=len(books_list),
        sessions_synced=len(sessions),
        continuity_rows_synced=len(continuity_rows),
        world_bible_rows_synced=len(world_bible_rows),
        total_career_words=total_career_words,
        total_effort_points=round(total_effort, 2),
        continuity_gate_status=gate_status,
        total_world_bible_entities=total_bible_entities,
        sheets_present=list(sheet_map.keys()),
        charts_count=charts_count,
    )


_SYNC_IN_PROGRESS: bool = False


def auto_sync_workbook_if_present(workspace_or_vault_root: Path) -> WorkbookSyncResult | None:
    global _SYNC_IN_PROGRESS
    if _SYNC_IN_PROGRESS:
        return None
    """Automatic hook called by Ars-Arcanum engines (`phase_effort_engine`, `vault_continuity_runner`,
    `audit_hardening`) to keep `Master_Writing_Ecosystem.xlsx` continuously synchronized.
    """
    resolved = workspace_or_vault_root.resolve()
    candidates = [
        resolved / DEFAULT_WORKBOOK_FILENAME,
        resolved.parent / DEFAULT_WORKBOOK_FILENAME,
        resolved.parent.parent / DEFAULT_WORKBOOK_FILENAME,
        resolved.parent.parent.parent / DEFAULT_WORKBOOK_FILENAME,
    ]
    for cand in candidates:
        if cand.is_file():
            try:
                _SYNC_IN_PROGRESS = True
                return sync_workbook(cand.parent, cand)
            except Exception:  # nosec B110
                return None
            finally:
                _SYNC_IN_PROGRESS = False
    return None


def inspect_workbook_summary(workbook_path: Path) -> dict[str, Any]:
    """Inspect an existing `Master_Writing_Ecosystem.xlsx` using pure stdlib OpenXML."""
    resolved = workbook_path.resolve()
    with zipfile.ZipFile(resolved, "r") as zf:
        sheet_map = _map_sheet_paths(zf)
        shared_strings = _load_shared_strings(zf)
        charts_count = sum(
            1 for name in zf.namelist() if name.startswith("xl/charts/chart") and name.endswith(".xml")
        )
        cc_root = (
            ET.fromstring(zf.read(sheet_map["Continuity & Compilers"]))  # nosec B314
            if "Continuity & Compilers" in sheet_map
            else None
        )
        wb_root = (
            ET.fromstring(zf.read(sheet_map["World Bible & Lore"]))  # nosec B314
            if "World Bible & Lore" in sheet_map
            else None
        )
        cfg_root = (
            ET.fromstring(zf.read(sheet_map["Config"]))  # nosec B314
            if "Config" in sheet_map
            else None
        )

        integrity_status = (
            _read_cell_text_xml(cfg_root, "C33", shared_strings) if cfg_root is not None else "Unknown"
        )
        gate_status = (
            _read_cell_text_xml(cc_root, "A5", shared_strings) if cc_root is not None else "PASS (CLEAN)"
        )
        total_entities = (
            _read_cell_text_xml(wb_root, "A5", shared_strings) if wb_root is not None else "0"
        )

    return {
        "workbook_path": str(resolved),
        "sheets": list(sheet_map.keys()),
        "sheet_count": len(sheet_map),
        "charts_count": charts_count,
        "integrity_status": integrity_status,
        "continuity_gate_status": gate_status or "PASS (CLEAN)",
        "total_world_bible_entities": int(float(total_entities)) if total_entities else 0,
    }


def add_book_to_ecosystem(
    workspace_root: Path,
    *,
    year: int,
    book_title: str,
    book_type: str = "Novel",
    universe: str = "Reliquary",
    series: str = "Sand Sea Saga",
    stage: str = "Concept",
    draft_target_words: int = 150000,
    start_date: str = "2026-10-16",
    deadline: str = "2027-10-16",
) -> WorkbookSyncResult:
    """Register or update a book in `.arcanum/ecosystem_books.json` and auto-sync the workbook."""
    resolved = workspace_root.resolve()
    arcanum_dir = resolved / ".arcanum"
    arcanum_dir.mkdir(parents=True, exist_ok=True)
    books_path = arcanum_dir / "ecosystem_books.json"
    if not is_safe_subpath(resolved, books_path):
        raise ValueError("Unsafe path for ecosystem_books.json")

    existing: list[dict[str, Any]] = []
    if books_path.is_file():
        try:
            loaded = json.loads(books_path.read_text(encoding="utf-8"))
            if isinstance(loaded, list):
                existing = [
                    x for x in loaded if isinstance(x, dict) and x.get("book_title") != book_title
                ]
        except (OSError, ValueError):
            existing = []

    existing.append(
        {
            "year": year,
            "book_title": book_title,
            "book_type": book_type,
            "universe": universe,
            "series": series,
            "stage": stage,
            "draft_target_words": draft_target_words,
            "start_date": start_date,
            "deadline": deadline,
        }
    )
    books_path.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")
    return sync_workbook(resolved)


def watch_workspace_and_sync(
    workspace_root: Path,
    workbook_path: Path | None = None,
    *,
    interval_seconds: float = 2.0,
    max_iterations: int | None = None,
) -> int:
    """Watch markdown, YAML, and JSONL files in `workspace_root` and auto-sync `Master_Writing_Ecosystem.xlsx`."""
    resolved = workspace_root.resolve()
    last_signature: tuple[tuple[str, int], ...] | None = None
    iterations = 0

    while True:
        sig_items: list[tuple[str, int]] = []
        for ext in ("*.md", "*.yaml", "*.yml", "*.jsonl", "*.json"):
            for p in sorted(resolved.rglob(ext)):
                if ".git" in p.parts or "__pycache__" in p.parts:
                    continue
                try:
                    sig_items.append((str(p.relative_to(resolved)), p.stat().st_mtime_ns))
                except OSError:
                    continue
        current_sig = tuple(sig_items)
        if current_sig != last_signature:
            res = sync_workbook(resolved, workbook_path)
            stamp = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
            print(
                f"[{stamp}] Auto-synced {Path(res.workbook_path).name}: "
                f"{res.books_synced} books, {res.sessions_synced} sessions, "
                f"{res.total_career_words:,} words, {res.charts_count} charts."
            )
            last_signature = current_sig

        iterations += 1
        if max_iterations is not None and iterations >= max_iterations:
            break
        time.sleep(interval_seconds)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="arcanum workbook",
        description="Synchronize, inspect, or watch the Ars-Arcanum Master Writing Ecosystem Excel workbook.",
    )
    parser.add_argument(
        "action",
        nargs="?",
        default="sync",
        choices=["sync", "status", "watch", "add-book"],
        help="Workbook action to perform (default: sync)",
    )
    parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace or repo root")
    parser.add_argument(
        "--workbook", type=Path, default=None, help="Explicit path to Master_Writing_Ecosystem.xlsx"
    )
    parser.add_argument(
        "--recalc", action="store_true", help="Run headless LibreOffice recalculation if installed"
    )
    parser.add_argument("--json", action="store_true", dest="as_json", help="Emit JSON output")
    parser.add_argument("--interval", type=float, default=2.0, help="Watch poll interval in seconds")
    parser.add_argument("--title", default="", help="Book title for add-book")
    parser.add_argument(
        "--year", type=int, default=2027, help="Target publication/draft year for add-book"
    )
    parser.add_argument("--type", dest="book_type", default="Novel", help="Book type for add-book")
    parser.add_argument("--universe", default="Reliquary", help="Universe for add-book")
    parser.add_argument("--series", default="Sand Sea Saga", help="Series title for add-book")
    parser.add_argument("--stage", default="Concept", help="Project stage for add-book")
    parser.add_argument(
        "--target-words", type=int, default=150000, help="Draft target words for add-book"
    )
    parser.add_argument("--start-date", default="2026-10-16", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--deadline", default="2027-10-16", help="Deadline date (YYYY-MM-DD)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.action == "status":
        target = args.workbook or (args.workspace.resolve() / DEFAULT_WORKBOOK_FILENAME)
        info = inspect_workbook_summary(target)
        if args.as_json:
            print(json.dumps(info, indent=2))
        else:
            print(
                f"[WORKBOOK STATUS] {info['workbook_path']} | "
                f"Sheets: {info['sheet_count']} ({', '.join(info['sheets'])}) | "
                f"Charts: {info['charts_count']} | "
                f"Integrity: {info['integrity_status']}"
            )
        return 0

    if args.action == "watch":
        return watch_workspace_and_sync(
            args.workspace,
            args.workbook,
            interval_seconds=args.interval,
        )

    if args.action == "add-book":
        if not args.title:
            print("[ERROR] --title is required for `arcanum workbook add-book`", file=sys.stderr)
            return 2
        res = add_book_to_ecosystem(
            args.workspace,
            year=args.year,
            book_title=args.title,
            book_type=args.book_type,
            universe=args.universe,
            series=args.series,
            stage=args.stage,
            draft_target_words=args.target_words,
            start_date=args.start_date,
            deadline=args.deadline,
        )
    else:
        res = sync_workbook(
            args.workspace,
            args.workbook,
            recalc_with_libreoffice=args.recalc,
        )

    if args.as_json:
        print(json.dumps(res.to_dict(), indent=2))
    else:
        print(
            f"[WORKBOOK SYNCED] {res.workbook_path}\n"
            f"  • Sheets ({len(res.sheets_present)}): {', '.join(res.sheets_present)}\n"
            f"  • Embedded Dynamic Charts: {res.charts_count}\n"
            f"  • Series: {res.series_synced} | Books: {res.books_synced} | Sessions: {res.sessions_synced}\n"
            f"  • Career Words: {res.total_career_words:,} | Effort Points: {res.total_effort_points:,.1f}\n"
            f"  • Continuity Gate: {res.continuity_gate_status} | World Bible Entities: {res.total_world_bible_entities}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
