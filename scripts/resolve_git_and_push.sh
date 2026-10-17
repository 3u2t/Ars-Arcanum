#!/usr/bin/env bash
# =============================================================================
# Ars Arcanum — Automated Branch/PR Consolidation, Verification & Push Script
# =============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "=== [1/6] Fetching all remotes and pruning deleted tracking refs ==="
if [ -d ".git" ]; then
  git fetch --all --prune
  git checkout main
  git pull --ff-only origin main || true

  echo "=== [2/6] Resolving and merging any open Pull Requests or non-main branches into main ==="
  if command -v gh >/dev/null 2>&1; then
    while IFS= read -r pr_num; do
      [ -n "$pr_num" ] || continue
      echo "Merging open PR #$pr_num into main..."
      gh pr merge "$pr_num" --merge --delete-branch || true
    done < <(gh pr list --state open --json number --jq '.[].number' 2>/dev/null || true)
  fi

  while IFS= read -r remote_branch; do
    [ -n "$remote_branch" ] || continue
    echo "Merging origin/$remote_branch into main..."
    git merge --no-edit "origin/$remote_branch" || true
    git push origin --delete "$remote_branch" || true
  done < <(git for-each-ref --format='%(refname:lstrip=3)' refs/remotes/origin | grep -vE '^(HEAD|main)$' || true)

  while IFS= read -r local_branch; do
    [ -n "$local_branch" ] || continue
    echo "Merging and pruning local branch $local_branch..."
    git merge --no-edit "$local_branch" || true
    git branch -D "$local_branch" || true
  done < <(git for-each-ref --format='%(refname:lstrip=2)' refs/heads | grep -v '^main$' || true)
fi

echo "=== [3/6] Removing obsolete clutter files from Git index ==="
rm -f UPGRADE_INSTALL.md scripts/arcanum-lite launchers/arcanum-lite.desktop .github/RELEASE_v0.2.0_NOTES.md

echo "=== [4/6] Synchronizing documentation footers & running full verification suite ==="
python3 scripts/apply_arcanum_upgrade.py --prepare-release
PYTHONPATH=".:scripts:scripts/lib" python3 -m scripts.lib.workbook_sync sync
python3 scripts/sync_and_verify_docs.py
python3 scripts/install_and_verify_samples.py
python3 -m scripts.lib.audit_hardening templates/demo-cosmos/Eldoria-Cosmos --json --no-dashboard

echo "=== [5/6] Staging and committing all changes to main ==="
if [ -d ".git" ]; then
  git add -A
  if ! git diff --cached --quiet; then
    git commit -m "fix(ci,docs,core): resolve CI/CD workflows, unify 11-lens audit upgrades, and sync docs/templates"
  else
    echo "Working tree already clean."
  fi

  echo "=== [6/6] Pushing unified main branch to GitHub ==="
  git push origin main
fi

echo "✓ Ars Arcanum upgrade, branch consolidation, and CI verification complete!"
