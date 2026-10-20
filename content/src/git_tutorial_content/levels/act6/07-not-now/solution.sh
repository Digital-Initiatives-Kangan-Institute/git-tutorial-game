#!/usr/bin/env bash
set -euo pipefail

#: A pull, stopped part way. And a rush note that is not committed yet.
git status

#: A commit now would finish the merge, rush note and all. Back out instead.
git merge --abort
git status

#: The rush note survived the abort: it was never part of the merge. Finish it.
python3 - <<'PY'
from pathlib import Path

path = Path("dispatch/2026-03-26.md")
text = path.read_text(encoding="utf-8")
path.write_text(text.rstrip("\n") + " 15:00 by the Fennick van.\n", encoding="utf-8")
PY
cat dispatch/2026-03-26.md

#: Commit it on its own.
git add dispatch/2026-03-26.md
git commit -m "Write up the Fennick rush order"

#: Now there is time. Pull again: it stops in the same place.
git pull --no-edit || true
git status

#: Marta's call: your 22 stands. You would edit the file by hand.
python3 - <<'PY'
import re
from pathlib import Path

path = Path("stock/aisle-b.md")
text = path.read_text(encoding="utf-8")
text = re.sub(r"<<<<<<< .*?\n.*?>>>>>>> .*?\n", "22 bundles counted.\n", text, flags=re.S)
path.write_text(text, encoding="utf-8")
PY

#: Settle, finish the merge, send everything up.
git add stock/aisle-b.md
git commit --no-edit
git push
git log --oneline --graph -n 5
