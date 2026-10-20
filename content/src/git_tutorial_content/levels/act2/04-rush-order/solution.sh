#!/usr/bin/env bash
set -euo pipefail

#: One file changed and not committed.
git status

#: Switching now is refused: the change would have nowhere to go.
git switch main || true

#: Lift the pending work off to one side. The working tree goes clean.
git stash
git status

#: Now the switch is allowed.
git switch main

#: Do the urgent job. You would add this line in your editor.
python3 - <<'PY'
from pathlib import Path

path = Path("dispatch/log.md")
anchor = "- Dispatch note for 3 March started.\n"
line = "- Rush order for Fennick Garden Centre dispatched.\n"
path.write_text(path.read_text(encoding="utf-8").replace(anchor, anchor + line),
                encoding="utf-8")
PY
git add dispatch/log.md
git commit -m "Log the Fennick rush order"

#: Back to your own branch, and take the work out of the stash again.
git switch stocktake-prep
git stash pop

#: Exactly where you left off, and the rush order is on main.
git status
git log --oneline --graph --all
