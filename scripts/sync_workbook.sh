#!/usr/bin/env bash
# ==============================================================================
# Ars Arcanum — Master Writing Ecosystem Workbook Auto-Sync Script
# Synchronizes Master_Writing_Ecosystem.xlsx with all vaults, books, sprint logs,
# continuity compilers, and World Bible entities across the repository.
# ==============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

export PYTHONPATH="${REPO_ROOT}:${REPO_ROOT}/scripts:${REPO_ROOT}/scripts/lib:${PYTHONPATH:-}"

python3 -m scripts.lib.workbook_sync "$@"
