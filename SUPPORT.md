# Support & Community Resources (`SUPPORT.md`)

Welcome to the Ars Arcanum support directory. Because Ars Arcanum is an offline-first sovereign system, comprehensive diagnostics and self-help tools are built directly into your local installation.

---

## 1. Quick Assistance & Onboarding

- **Non-Technical & Zero-CLI Writers**:
  - Run the automated setup: double-click [`launchers/setup_windows.bat`](launchers/setup_windows.bat).
  - Launch the visual studio cockpit: double-click [`launchers/launch_studio.bat`](launchers/launch_studio.bat).
  - Open the 15-minute quickstart guide: [`docs/START_HERE.md`](docs/START_HERE.md).
- **Fast Command Reference**:
  - Review the CLI cheatsheet: [`docs/CHEATSHEET.md`](docs/CHEATSHEET.md).
- **Comprehensive Authoring Manual**:
  - Consult the complete novelist and worldbuilder guide: [`docs/AUTHOR_MANUAL.md`](docs/AUTHOR_MANUAL.md).

---

## 2. Automated Self-Diagnosis & Doctor Engine

If you encounter toolchain errors, missing compilers, or unexpected behavior:

1. **Run the World Doctor**:
   ```bash
   python scripts/arcanum doctor
   ```
   This will inspect:
   - Python version and runtime compatibility ($\ge 3.10$).
   - Git repository status and branch integrity.
   - Optional publication compilers (`typst`, `pandoc`).
   - Linter and type-checking toolchain (`ruff`, `mypy`).
   - Filesystem atomic durability and advisory lock availability.
2. **Export a Redacted Bug Report Bundle**:
   If reporting an issue to maintainers, generate an anonymized diagnostic bundle:
   ```bash
   python scripts/arcanum doctor --bundle bug_report.zip
   ```
   *Privacy Guarantee*: The diagnostic bundler automatically sanitizes all manuscript prose, author identities, and private tokens before bundling logs and toolchain metadata into the archive.

---

## 3. Documentation Directory Map

Consult the [3-Tier Documentation Index (`docs/INDEX.md`)](docs/INDEX.md) for navigation across 70+ specialized manuals:
- **Tier 1 (Zero-Friction Quickstart)**: [`docs/START_HERE.md`](docs/START_HERE.md), [`docs/LITE_MODE.md`](docs/LITE_MODE.md), [`docs/codebase/INTEGRATIONS.md`](docs/codebase/INTEGRATIONS.md), [`docs/CHEATSHEET.md`](docs/CHEATSHEET.md).
- **Tier 2 (Author Craft & Worldbuilding)**: [`docs/AUTHOR_MANUAL.md`](docs/AUTHOR_MANUAL.md), [`docs/WRITING_SPRINT.md`](docs/WRITING_SPRINT.md), [`docs/WORD_COUNTER.md`](docs/WORD_COUNTER.md), [`docs/THEME_STUDIO.md`](docs/THEME_STUDIO.md), [`docs/EPISTEMIC_FIREWALL.md`](docs/EPISTEMIC_FIREWALL.md), [`docs/TIMELINE_SOLVER.md`](docs/TIMELINE_SOLVER.md), [`docs/CONLANG_LINTER.md`](docs/CONLANG_LINTER.md), [`docs/RESOURCE_LEDGER.md`](docs/RESOURCE_LEDGER.md).
- **Tier 3 (Engine Internals & Architecture)**: [`docs/codebase/ARCHITECTURE.md`](docs/codebase/ARCHITECTURE.md), [`docs/codebase/STRUCTURE.md`](docs/codebase/STRUCTURE.md), [`docs/codebase/TESTING.md`](docs/codebase/TESTING.md), [`docs/codebase/STACK.md`](docs/codebase/STACK.md), [`docs/codebase/CONVENTIONS.md`](docs/codebase/CONVENTIONS.md), [`docs/codebase/CONCERNS.md`](docs/codebase/CONCERNS.md), [`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md), [`AGENTS.md`](AGENTS.md).

---

## 4. Getting Help & Reporting Issues

- **Bug Reports**: Open an issue on GitHub. Please attach the redacted diagnostic bundle from `arcanum doctor --bundle`.
- **Feature Requests & Creative Discussions**: Share worldbuilding workflows and craft suggestions in GitHub Discussions.
- **Security Vulnerabilities**: Report security issues privately per the instructions in [`SECURITY.md`](SECURITY.md).
