#!/usr/bin/env bash
set -euo pipefail

#: Start by catching up. Nothing of yours is in the way, so it is a
#: fast-forward: no merge, no commit, main just moves.
git pull
git log --oneline -n 2

#: Now the morning's work.
python3 - <<'PY'
from pathlib import Path

path = Path("dispatch/log.md")
text = path.read_text(encoding="utf-8")
path.write_text(
    text.replace(
        "- Returns procedure started.\n",
        "- Returns procedure started.\n- B-15 cartons counted.\n",
    ),
    encoding="utf-8",
)
PY

git add dispatch/log.md
git commit -m "Note the B-15 count in the log"

#: And send it up before you get distracted.
git push
git status
git log --oneline --graph --all
