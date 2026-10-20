#!/usr/bin/env bash
set -euo pipefail

#: Head Office's branch has your commit and nothing of hers.
git log --oneline --graph --all
git log --oneline origin/stocktake-plan

#: Remote-tracking branches keep a reflog of their own.
git reflog show origin/stocktake-plan

#: The line before your forced push is where the remote was: her commit.
HERS=""
for sha in $(git reflog show origin/stocktake-plan --format='%H'); do
  if [ "$(git log -1 --format=%s "$sha")" = "Book the stocktake date in the log" ]; then
    HERS=$sha
    break
  fi
done
git log --oneline -n 2 "$HERS"

#: Bring it back into your branch. Her commit, not a copy of it.
git merge --no-edit "$HERS"

#: And push, without forcing anything this time.
git push
git log --oneline --graph --all
git status
