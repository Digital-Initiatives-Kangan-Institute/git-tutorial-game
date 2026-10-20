#!/usr/bin/env bash
set -euo pipefail

#: Your counts are committed, scratch file and all. Pull.
git pull --no-edit || true

#: Two modify/delete conflicts: both sheets deleted by Head Office.
git status

#: Agree with both retirements.
git rm stock/aisle-e-overflow.md stock/seasonal-twine.md

#: The scanner dump was never a record. Stop tracking it, but keep it on disk.
git rm --cached stocktake.tmp
ls stocktake.tmp

#: And make sure it does not get added again.
echo stocktake.tmp >> .gitignore
git add .gitignore
git status

#: One commit finishes the merge and carries the tidy-up.
git commit --no-edit
git push
git status
git log --oneline --graph -n 4
