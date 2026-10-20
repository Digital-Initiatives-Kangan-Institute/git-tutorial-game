#!/usr/bin/env bash
set -euo pipefail

#: Your deletion is committed. Pull Head Office's changes.
git pull --no-edit || true

#: delete/modify: you deleted the sheet, Ines changed it. "deleted by us".
git status
git log --merge --oneline

#: Ines's version is current procedure. Take it whole.
git restore --theirs docs/receiving.md
cat docs/receiving.md

#: Adding it settles the conflict on the side of keeping it.
git add docs/receiving.md
git status
git commit --no-edit
git push
git log --oneline --graph -n 4
