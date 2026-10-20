#!/usr/bin/env bash
set -euo pipefail

#: Your notes say Head Office still has aisle-c-count.
git branch -r

#: Fetch and prune: origin/main moves on, the stale name goes.
git fetch --prune
git branch -r

#: Bring main up to date with what Head Office now has.
git pull
git log --oneline --graph -n 4

#: The merge commit at the top: Theo's work, folded in by Ines.
git log -1
wt answer merged_by "$(git log -1 --format=%an | cut -d' ' -f1)"
git status
