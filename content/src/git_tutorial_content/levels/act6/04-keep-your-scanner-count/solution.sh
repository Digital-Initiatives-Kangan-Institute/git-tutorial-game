#!/usr/bin/env bash
set -euo pipefail

#: Your scan is committed. Pull Theo's paper count.
git pull --no-edit || true
git status

#: The scan is the newer count: take your own side of the stock sheet, whole.
git restore --ours stock/aisle-b.md
cat stock/aisle-b.md

#: HEAD is still your commit during the merge, so nothing differs from it.
git diff HEAD -- stock/aisle-b.md

#: Settle it and finish the merge.
git add stock/aisle-b.md
git commit --no-edit

#: Theo's log line came in on its own.
grep "paper count" dispatch/log.md
git push
git log --oneline --graph -n 4
