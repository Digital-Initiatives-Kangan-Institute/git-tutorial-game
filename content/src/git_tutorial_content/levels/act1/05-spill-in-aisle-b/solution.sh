#!/usr/bin/env bash
set -euo pipefail

#: Two changes. Status names the files; the diffs show which is where.
git status

#: Not staged: the scribble on the aisle B sheet.
git diff

#: Staged: the duplicated pallet-wrap block.
git diff --staged

#: The aisle B sheet was never staged, so one command puts it back.
git restore stock/aisle-b.md

#: The price list is in both places. Unstage it first.
git restore --staged suppliers/price-list.md

#: Then overwrite the file on disk from the staging area.
git restore suppliers/price-list.md

#: Nothing pending, and the history never moved.
git status
git log --oneline -1
