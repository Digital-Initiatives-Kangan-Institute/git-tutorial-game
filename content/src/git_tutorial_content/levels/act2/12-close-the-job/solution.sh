#!/usr/bin/env bash
set -euo pipefail

#: Both sides touched both files.
git log --oneline --graph --all

#: Start it. This time two files come back unresolved.
git merge aisle-d-signoff || true
git status

#: The dispatch log wants both lines: nobody has to lose an entry.
python3 - <<'PY'
import re
from pathlib import Path

path = Path("dispatch/log.md")
text = path.read_text(encoding="utf-8")
both = "- Fennick order dispatched.\n- Aisle D fit-out signed off.\n"
text = re.sub(r"<<<<<<< .*?\n.*?>>>>>>> .*?\n", both, text, flags=re.S)
path.write_text(text, encoding="utf-8")
PY

#: The README needs one line that covers what both sides meant.
python3 - <<'PY'
import re
from pathlib import Path

path = Path("README.md")
text = path.read_text(encoding="utf-8")
agreed = "Deliveries outside these hours wait by gate 2 or in aisle D. Yard phone: 01632 960142.\n"
text = re.sub(r"<<<<<<< .*?\n.*?>>>>>>> .*?\n", agreed, text, flags=re.S)
path.write_text(text, encoding="utf-8")
PY

#: Stage each one as it is settled, and watch the list shrink.
git add dispatch/log.md
git status
git add README.md
git status

#: Empty list, so the merge can be finished.
git commit --no-edit
git log --oneline --graph --all
