#!/usr/bin/env bash
set -euo pipefail

#: The close-down is finished on peak-close. Theo has been at main since.
git status
git fetch --prune
git log --oneline --graph --all -n 6

#: Bring main up to date, then fold the branch in on top.
git switch main
git pull
git merge --no-edit peak-close

#: Send main up before sealing anything.
git push

#: Seal the end of the season on the commit Head Office now has.
git tag peak-2025
git push origin peak-2025

#: The work is safe in main. Take the branch down here and there.
git branch -d peak-close
git push origin --delete peak-close

git log --oneline --graph --decorate --all -n 6
git status
