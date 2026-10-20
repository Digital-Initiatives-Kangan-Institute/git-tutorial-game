#!/usr/bin/env bash
set -euo pipefail

#: Three commits. The oldest of them books in a price nobody agreed.
git log --oneline -n 4

#: Find it by what it did, rather than by counting backwards.
BAD=$(git log -n 1 --format=%H --grep='Update the pallet wrap price')
git show --stat "$BAD"

#: Undo it with a new commit. Nothing already in the history changes.
git revert --no-edit "$BAD"

#: The price is right again, and the two commits after it are untouched.
git log --oneline -n 5
git diff HEAD~1 HEAD
git status
