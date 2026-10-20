#!/usr/bin/env bash
set -euo pipefail

#: Your rota is committed. Pull before sending it.
git pull --no-edit || true

#: add/add: both sides created the same file.
git status

#: Whose is the other draft? log --merge lists both commits.
git log --merge
wt answer who "$(git log -1 --format=%an MERGE_HEAD | cut -d' ' -f1)"

#: Both drafts are fenced off in the file.
cat rota/easter.md

#: Neither is wrong: keep every line from both, markers out. You would edit by hand.
python3 - <<'PY'
import re
from pathlib import Path

path = Path("rota/easter.md")
text = path.read_text(encoding="utf-8")
block = re.compile(r"<<<<<<< .*?\n(.*?)=======\n(.*?)>>>>>>> .*?\n", re.S)
text = block.sub(lambda m: m.group(2) + m.group(1), text)
path.write_text(text, encoding="utf-8")
PY
cat rota/easter.md

#: Settled. Finish the merge and send it up.
git add rota/easter.md
git commit --no-edit
git push
git log --oneline --graph -n 4
