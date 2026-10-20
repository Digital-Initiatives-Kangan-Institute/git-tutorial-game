#!/usr/bin/env bash
set -euo pipefail

#: The fit-out is finished on its own branch, and already at Head Office.
git status
git log --oneline --graph --all -n 5

#: Merge into main, from main. Take Head Office's updates first.
git switch main
git pull
git merge --no-edit aisle-e-fitout

#: Send main up, so the work is safe at Head Office before any deleting.
git push

#: Now the branch name has nothing left to do. Clear it here, then there.
git branch -d aisle-e-fitout
git push origin --delete aisle-e-fitout
git branch -a
git status
