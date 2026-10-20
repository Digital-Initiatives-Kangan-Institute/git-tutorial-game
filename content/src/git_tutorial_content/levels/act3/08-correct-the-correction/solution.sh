#!/usr/bin/env bash
set -euo pipefail

#: Three commits: the discount, its log line, and the revert.
git log --oneline -n 4

#: What the revert took out.
REVERT=$(git log -n 1 --format=%H --grep='Revert "Add the Kestrelby bulk discount"')
git show "$REVERT"

#: Undo the undo. A revert is a commit like any other.
git revert --no-edit "$REVERT"

#: The discount is back, and all three steps are in the log.
git log --oneline -n 5
cat suppliers/price-list.md
