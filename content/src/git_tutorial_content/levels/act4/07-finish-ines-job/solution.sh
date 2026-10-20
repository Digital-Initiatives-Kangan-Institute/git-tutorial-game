#!/usr/bin/env bash
set -euo pipefail

#: Your repository has never heard of her branch.
git branch -r

#: Read the bulletin.
git fetch
git branch -r

#: No -c: git sees the remote branch and makes you a local one paired with it.
git switch returns-procedure
git status

#: Finish the sentence she left hanging.
python3 - <<'PY'
from pathlib import Path

path = Path("docs/receiving.md")
text = path.read_text(encoding="utf-8")
path.write_text(
    text.replace(
        "Returned pallets are booked in against\n",
        "Returned pallets are booked in against the original delivery note.\n",
    ),
    encoding="utf-8",
)
PY

git add docs/receiving.md
git commit -m "Finish the returns sentence"

#: Back to Head Office, on her branch, on top of her commit.
git push
git log --oneline -n 2
