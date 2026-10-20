#!/usr/bin/env bash
set -euo pipefail

#: The commit is made, and it is missing a line.
git log --oneline -n 2
git show --stat HEAD

#: Move the branch back one, and keep everything the commit held, staged.
git reset --soft HEAD~1

#: Nothing was lost: it is all sitting in the staging area.
git status
git diff --staged

#: Add the line that should have been in it.
python3 - <<'PY'
from pathlib import Path

path = Path("dispatch/log.md")
text = path.read_text(encoding="utf-8")
path.write_text(
    text.replace(
        "- Fennick Garden Centre order dispatched.\n",
        "- Fennick Garden Centre order dispatched.\n- Third pallet marked fragile.\n",
        1,
    ),
    encoding="utf-8",
)
PY

#: One commit, saying everything it should have said the first time.
git add dispatch/log.md
git commit -m "Log the Fennick dispatch"
git log --oneline -n 2
