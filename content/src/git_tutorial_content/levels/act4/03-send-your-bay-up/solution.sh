#!/usr/bin/env bash
set -euo pipefail

#: A branch for the work, as before.
git switch -c count-b15

#: The count Ines asked for.
python3 - <<'PY'
from pathlib import Path

path = Path("stock/aisle-b.md")
text = path.read_text(encoding="utf-8")
path.write_text(
    text.replace(
        "**B-15 Cartons, double wall**\n\nNot counted yet.\n",
        "**B-15 Cartons, double wall**\n\n12 bundles in stock.\n",
    ),
    encoding="utf-8",
)
PY

git add stock/aisle-b.md
git commit -m "Count the B-15 cartons"

#: Still only here. Nobody else can see it.
git log --oneline -n 1

#: Send it up, and record where it belongs.
git push -u origin count-b15

#: Head Office has the branch, and status now talks about both copies.
git status
git branch -vv
