# Ars Arcanum Complete Refactor & Feature Upgrade Pack

This archive mirrors the exact directory structure of `https://github.com/aryansinghnagar/Ars-Arcanum`.

## 30-Second Copy-Paste Installation

1. Extract `Ars-Arcanum-Upgrade-Pack.zip` and copy its contents directly into the root of your local `Ars-Arcanum` checkout:
   ```bash
   unzip Ars-Arcanum-Upgrade-Pack.zip -d /tmp/arcanum-upgrade
   cp -R /tmp/arcanum-upgrade/Ars-Arcanum/* /path/to/your/Ars-Arcanum/
   cp -R /tmp/arcanum-upgrade/Ars-Arcanum/.github /path/to/your/Ars-Arcanum/
   ```
2. Run the automated wiring and verification script:
   ```bash
   cd /path/to/your/Ars-Arcanum
   python3 scripts/apply_arcanum_upgrade.py
   ```
3. Commit and push:
   ```bash
   git add scripts/ src/ tests/ docs/ .github/ mypy.ini UPGRADE_INSTALL.md
   git commit -m "feat(core,worldbuilding): complete Phase 1-3 refactor and add 6 deterministic continuity engines"
   git push origin main
   ```
