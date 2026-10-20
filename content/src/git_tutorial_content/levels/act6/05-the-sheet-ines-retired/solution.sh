#!/usr/bin/env bash
set -euo pipefail

#: Your first-aid line is committed. Pull Head Office's changes.
git pull --no-edit || true

#: A modify/delete conflict: you changed the sheet, Ines deleted it.
git status

#: Who removed it, and why? log --merge shows both commits.
git log --merge --stat -n 2

#: Agree with the retirement: delete it and stage the deletion in one step.
git rm docs/opening-checks.md
git status

#: Finish the merge and send it up.
git commit --no-edit
git push
git log --oneline --graph -n 4
