#!/usr/bin/env bash
set -euo pipefail

#: Unfinished work in front of you, and an urgent typo to fix.
git status
grep -n "delivary" docs/receiving.md

#: Put the pending work aside first. Nothing else can happen until you do.
git stash
git status

#: The fix does not belong on main, so go to main and branch from there.
git switch main
git switch -c typo-fix

#: Fix it. You would do this in your editor.
python3 - <<'PY'
from pathlib import Path

path = Path("docs/receiving.md")
text = path.read_text(encoding="utf-8")
path.write_text(text.replace("delivary note", "delivery note"), encoding="utf-8")
PY
git add docs/receiving.md
git commit -m "Fix a typo in the receiving procedure"

#: Back to your own work, and take it out of the stash.
git switch stocktake-prep
git stash pop

#: Where you were, with the fix waiting on its own branch.
git status
git log --oneline --graph --all
