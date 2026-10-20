#!/usr/bin/env bash
set -euo pipefail

#: Two commits of yours, not yet sent. Pull before pushing.
git log --oneline -n 3
git pull --no-edit || true

#: Read before you fix. Which files are held?
git status
files=$(git diff --name-only --diff-filter=U | wc -l | tr -d ' ')

#: How many blocks, across both files?
grep -c '^<<<<<<<' stock/aisle-b.md suppliers/price-list.md || true
blocks=$(cat stock/aisle-b.md suppliers/price-list.md | grep -c '^<<<<<<<')

#: Whose commits disagree? log --merge lists both sides' commits on those files.
git log --merge --oneline
commits=$(git log --merge --oneline | wc -l | tr -d ' ')

wt answer files "$files"
wt answer blocks "$blocks"
wt answer commits "$commits"

#: Counts are yours, prices are Head Office's. You would edit both files by hand.
python3 - <<'PY'
import re
from pathlib import Path

def settle(path, keep):
    text = Path(path).read_text(encoding="utf-8")
    block = re.compile(r"<<<<<<< .*?\n(.*?)=======\n(.*?)>>>>>>> .*?\n", re.S)
    text = block.sub(lambda m: m.group(1) if keep == "mine" else m.group(2), text)
    Path(path).write_text(text, encoding="utf-8")

settle("stock/aisle-b.md", "mine")
settle("suppliers/price-list.md", "theirs")
PY
cat stock/aisle-b.md suppliers/price-list.md

#: Both settled. Add them, finish the merge, send it up.
git add stock/aisle-b.md suppliers/price-list.md
git status
git commit --no-edit
git push
git log --oneline --graph -n 6
