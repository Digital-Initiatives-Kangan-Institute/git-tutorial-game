#!/usr/bin/env bash
set -euo pipefail

#: Your commit is ready. Head Office refuses it: Theo got there first.
git status
git push || true

#: Take Theo's commit, merged with yours, then send both.
git pull --no-edit
git push

#: Pulling did not take down the stale name for Ines's withdrawn draft.
git branch -r
git fetch --prune
git branch -r

#: Everything agrees, and nothing is listed that is not there.
git log --oneline --graph --all -n 5
git status
