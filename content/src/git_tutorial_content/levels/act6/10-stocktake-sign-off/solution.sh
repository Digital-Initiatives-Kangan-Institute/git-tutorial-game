#!/usr/bin/env bash
set -euo pipefail

#: Your scan and your checklist tick are committed. Pull everything from Head Office.
git log --oneline -n 3
git pull --no-edit || true

#: Read before you fix: three files, three kinds of conflict.
git status

#: Whose commits are on the other side? log --merge lists them with authors.
git log --merge --format='%h %an: %s'
wt answer prices "$(git log -1 --format=%an MERGE_HEAD -- suppliers/price-list.md | cut -d' ' -f1)"

#: Aisle B needs both sides: Theo's B-14, your B-15. You would edit it by hand.
cat stock/aisle-b.md
python3 - <<'PY'
import re
from pathlib import Path

path = Path("stock/aisle-b.md")
text = path.read_text(encoding="utf-8")
text = re.sub(r"<<<<<<< .*?\n.*?>>>>>>> .*?\n",
              "38 rolls counted.\n\n**B-15 Cartons, double wall**\n\n26 bundles counted.\n",
              text, flags=re.S)
path.write_text(text, encoding="utf-8")
PY
cat stock/aisle-b.md
git add stock/aisle-b.md

#: The price list is Head Office's, whole.
git restore --theirs suppliers/price-list.md
git add suppliers/price-list.md

#: The checklist is retired.
git rm docs/stocktake-checklist.md

#: Nothing left held. Finish the merge and send it up.
git status
git commit --no-edit
git push

#: Seal the commit Head Office now has, and send the seal.
git tag stocktake-final
git push origin stocktake-final
git log --oneline --graph --decorate -n 6
