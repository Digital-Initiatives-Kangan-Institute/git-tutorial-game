#!/usr/bin/env bash
set -euo pipefail

#: Two changed files, and they are not in the same state.
git status

#: One is staged, one is not.
git diff --staged
git diff

#: Stash takes every pending change, both of them, in one go.
git stash
git status

#: Go and look at main. Nothing here is yours to change.
git switch main
git log --oneline -3

#: Back, and take the work out again.
git switch aisle-b-count
git stash pop

#: Both edits are back. Nothing was lost and nothing was committed.
git status

#: Now finish what you were interrupted in the middle of.
git add stock/aisle-b.md dispatch/log.md
git commit -m "Count the cartons in B-15"
git status
