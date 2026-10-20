#!/usr/bin/env bash
set -euo pipefail

#: Paused mid-merge. Read which branch is coming in before fixing anything.
git status

#: month-end. That is Theo's month close, not the fix you wanted.
git log --oneline --graph --all

#: So do not resolve it. Back out of the whole attempt.
git merge --abort
git status

#: The branch you meant. Different file, so it combines on its own.
git merge --no-edit hotfix

#: The fix is in, and the month close is still waiting on its branch.
git log --oneline --graph --all
cat suppliers/price-list.md
