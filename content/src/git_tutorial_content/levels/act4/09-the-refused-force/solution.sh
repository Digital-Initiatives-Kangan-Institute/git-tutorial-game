#!/usr/bin/env bash
set -euo pipefail

#: Your commit was rewritten, so Head Office's branch cannot move to it.
git log --oneline -n 2
git push || true

#: The safer force. It refuses, and the reason is worth reading.
git push --force-with-lease || true

#: "Stale info" means Head Office moved since you last looked. So look.
git fetch
git log --oneline --graph --all

#: Ines booked the date. Forcing would have deleted that.
git log --oneline origin/stocktake-plan

#: Both are wanted, so combine them and push without forcing anything.
git merge --no-edit origin/stocktake-plan
git push
git status
