# Ars Arcanum Platform & Environment Support Matrix

This document defines the formal compatibility, architecture tiers, and display server support for **Ars Arcanum**.

---

## 1. Operating System Tiers

| Environment | Version | Desktop / Terminal Interface | Architecture | Support Tier | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Linux Mint** | 22 (Wilma) / 21.x | XFCE (Primary Reference) / GTK3 | x86_64 / ARM64 | **Tier 1** | Target Reference Platform (Desktop + CLI) |
| **Ubuntu Desktop** | 24.04 LTS (Noble) / 22.04 LTS | GNOME / XFCE / GTK3 | x86_64 / ARM64 | **Tier 1** | CI Reference & Fully Supported |
| **Debian** | 13 (Trixie) / 12 (Bookworm) | XFCE / GTK3 | x86_64 / ARM64 | **Tier 1** | Fully Supported |
| **Windows** | 10 / 11 | PowerShell / Windows Terminal / Studio Cockpit / Double-Click Launchers (`launchers/launch_studio.bat`) | x86_64 / ARM64 | **Tier 1** | Pure Python CLI, 1-Click Launchers, Visual Studio, Zen Studio, Native EPUB3, and `pip install .` |
| **macOS** | 13+ (Ventura, Sonoma, Sequoia) | Terminal / Studio Cockpit / Zen Studio | Apple Silicon / Intel | **Tier 1** | Pure Python CLI, Studio Cockpit, Zen Studio, Engines & `pip install .` |
| **Fedora / RHEL** | 39 / 40 / 41 | GNOME / XFCE | x86_64 | **Tier 2** | Supported via DNF & RPM spec (`pkg/rpm/`) |
| **Arch Linux / Manjaro** | Rolling | Any | x86_64 | **Tier 2** | Supported via Pacman & AUR PKGBUILD (`pkg/arch/`) |
| **openSUSE** | Tumbleweed / Leap | Any | x86_64 | **Tier 2** | Supported via Zypper |

### Tier Definitions
- **Tier 1 (Target Reference & Cross-Platform Python Core)**: Fully verified through automated test suites (692 tests passing at 100%), packaging builds (`pip install .`), Visual Studio Cockpit (`127.0.0.1:4242`), Zen Studio, Windows double-click launchers (`launchers/launch_studio.bat`, `launchers/setup_windows.bat`), and all craft engines. Linux provides native GTK3 desktop menus, system launchers, and shell wrappers (`scripts/arcanum`).
- **Tier 2 (Compatible Distributions)**: Supported via distro package specs and `--force` flag in shell setup scripts. Package manager variations are handled gracefully by fallback routines.

---

## 2. Display Server & Desktop Integration

| Component | X11 | Wayland | Windows / macOS | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **PyGObject GTK3 Desktop GUI** | :white_check_mark: Verified | :white_check_mark: Supported | :warning: Requires X11 / GTK stack | Native Linux desktop GUI |
| **Studio Cockpit (Webview)** | :white_check_mark: Verified | :white_check_mark: Supported | :white_check_mark: Native Browser | Standalone offline browser cockpit (`127.0.0.1:4242`) |
| **Zen Drafting Studio** | :white_check_mark: Verified | :white_check_mark: Supported | :white_check_mark: Native Browser | Standalone offline typewriter interface |
| **Windows Launchers** | N/A | N/A | :white_check_mark: Verified | `launchers/launch_studio.bat`, `setup_windows.bat` |
| **Zenity Dialogs** | :white_check_mark: Verified | :white_check_mark: Supported | N/A | Detected via `$WAYLAND_DISPLAY` / `$DISPLAY` |
| **Desktop Launchers** (`.desktop`) | :white_check_mark: Verified | :white_check_mark: Supported | N/A | Installed to `~/.local/share/applications` |
| **Notifications** (`notify-send`) | :white_check_mark: Verified | :white_check_mark: Supported | N/A | Standard `org.freedesktop.Notifications` |
| **Focus Mode** (FocusWriter) | :white_check_mark: Verified | :white_check_mark: Supported | Optional | Native Qt fullscreen support |

---

## 3. Hardware Baseline Recommendations

| Resource | Minimum | Recommended |
| :--- | :--- | :--- |
| **CPU** | 64-bit Dual Core (Intel / AMD / ARM64) | Intel Core i5-1335U or AMD Ryzen 5 / Apple Silicon M-series |
| **RAM** | 4 GB | 16 GB |
| **Storage** | 10 GB free space | 50 GB+ NVMe SSD (with LUKS or BitLocker Full-Disk Encryption) |
| **Display** | 1366 × 768 | 1920 × 1080 (FHD) or higher |
| **External Media** | USB Flash Drive | Dedicated USB 3.0 External SSD/HDD for 3-2-1 backups |

---

## Production CLI & Continuity Cross-Reference

| Capability | Command | Native Engine | Compatibility Facade |
| :--- | :--- | :--- | :--- |
| **Visual Studio Cockpit** | `python scripts/arcanum studio [VAULT] [--port 4242]` | `src.arcanum.server.daemon` | `scripts/lib/studio_server.py` |
| **Unified Continuity Suite** | `python scripts/arcanum continuity-suite [VAULT]` | `src.arcanum.worldbible.runner` | `scripts/lib/vault_continuity_runner.py` |
| **Phase-Aware Effort Points** | `python scripts/arcanum sprint-effort [ARGS]` | `src.arcanum.manuscript.velocity` | `scripts/lib/phase_effort_engine.py` |
| **Epistemic POV Firewall** | `python scripts/arcanum validate-epistemic [VAULT]` | `src.arcanum.worldbible.epistemics` | `scripts/lib/epistemic_firewall.py` |
| **Timeline & Route Physics** | `python scripts/arcanum timeline-audit [VAULT]` | `src.arcanum.worldbible.timeline` | `scripts/lib/timeline_solver.py` |
| **PolyGlot Conlang Linter** | `python scripts/arcanum conlang-check [ARGS]` | `src.arcanum.worldbible.conlang` | `scripts/lib/conlang_linter.py` |
| **Resource Conservation Ledger** | `python scripts/arcanum ledger-audit [VAULT]` | `src.arcanum.worldbible.ledger` | `scripts/lib/resource_ledger.py` |
| **Multi-POV Narrative Braid** | `python scripts/arcanum braid [MANUSCRIPT]` | `src.arcanum.manuscript.braid` | `scripts/lib/narrative_braid.py` |
| **Prose Word & Dialogue Metrics** | `python scripts/arcanum count-words [FILE/VAULT]` | `src.arcanum.manuscript.word_counter` | `scripts/lib/word_counter.py` |
| **Fast Paragraph Diff & Scraps** | `python scripts/arcanum diff-fast OLD.md NEW.md` | `src.arcanum.manuscript.diff` | `scripts/lib/diff_core.py` |
| **Word Tracked Changes Sync** | `python scripts/arcanum docx-tracked [export/pull]` | `src.arcanum.publishing.docx` | `scripts/lib/docx_tracked_changes.py` |
| **Multi-Format Publishing** | `python scripts/arcanum publish [MANUSCRIPT] --format ...` | `src.arcanum.publishing.publisher` | `scripts/lib/publisher.py` |
| **System Diagnostics & Doctor** | `python scripts/arcanum doctor [VAULT]` | `src.arcanum.core.diagnostics` | `scripts/lib/diagnostics.py` |
| **Schema Migration Engine** | `python scripts/arcanum migrate [VAULT]` | `src.arcanum.core.migrate` | `scripts/lib/migrate.py` |

