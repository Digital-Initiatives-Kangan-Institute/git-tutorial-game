#!/usr/bin/env bash
set -euo pipefail

#: Both branches changed the same count. Look before you start.
git log --oneline --graph --all

#: Start the merge. It stops part way and says which file it cannot settle.
git merge recount-b14 || true

#: status says the same thing, with the ways out underneath.
git status

#: Git wrote both versions into the file, fenced off with marker lines.
cat stock/aisle-b.md

#: Decide. You would edit the file; this writes the agreed count.
python3 - <<'PY'
import re
from pathlib import Path

path = Path("stock/aisle-b.md")
text = path.read_text(encoding="utf-8")
settled = "38 rolls, confirmed by a second recount.\n"
# Replace the whole conflicted region, markers included.
text = re.sub(r"<<<<<<< .*?\n.*?>>>>>>> .*?\n", settled, text, flags=re.S)
path.write_text(text, encoding="utf-8")
PY

#: No markers left, and the count reads as one line.
cat stock/aisle-b.md

#: Staging the file is how you tell git this one is settled.
git add stock/aisle-b.md
git status

#: Finish the merge. --no-edit accepts the message git already wrote.
git commit --no-edit
git log --oneline --graph --all
