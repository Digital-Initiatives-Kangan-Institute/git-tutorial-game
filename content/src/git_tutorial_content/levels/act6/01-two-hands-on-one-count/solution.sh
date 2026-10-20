#!/usr/bin/env bash
set -euo pipefail

#: Your count is committed. Take Head Office's news before sending it up.
git status
git log --oneline -n 2

#: The pull fetches Theo's commit and starts the merge. It stops part way.
git pull --no-edit || true

#: status names the file it could not settle.
git status

#: Both figures are in the file, fenced off by marker lines.
cat stock/aisle-b.md

#: Marta's figure replaces the whole block, markers included. You would edit the file.
python3 - <<'PY'
import re
from pathlib import Path

path = Path("stock/aisle-b.md")
text = path.read_text(encoding="utf-8")
settled = "38 rolls counted for the stocktake.\n"
text = re.sub(r"<<<<<<< .*?\n.*?>>>>>>> .*?\n", settled, text, flags=re.S)
path.write_text(text, encoding="utf-8")
PY
cat stock/aisle-b.md

#: Staging it says this file is settled. Committing finishes the merge.
git add stock/aisle-b.md
git commit --no-edit

#: Now main contains Theo's commit, so the push is accepted.
git push
git log --oneline --graph -n 4
git status
