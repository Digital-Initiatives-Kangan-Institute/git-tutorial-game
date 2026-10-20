#!/usr/bin/env bash
set -euo pipefail

#: What is where: one file changed, and three commits above the anchor.
git status
git log --oneline -n 4

#: Never committed, so there is nothing in the history to undo.
git restore stock/aisle-b.md
git status

#: The WIP commit is the newest and is yours alone. Move the label past it.
git log --oneline -n 2
git reset --hard HEAD~1

#: The price commit is shared, so it gets a commit that undoes it.
BAD=$(git log -n 1 --format=%H --grep='Update the pallet wrap price')
git revert --no-edit "$BAD"

#: Three commits on the anchor, nothing pending, aisle B as committed.
git log --oneline -n 4
git status
