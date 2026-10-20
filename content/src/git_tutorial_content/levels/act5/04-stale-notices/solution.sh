#!/usr/bin/env bash
set -euo pipefail

#: What your repository thinks Head Office has: main and four branches.
git branch -r

#: A plain fetch changes nothing here. It never removes a name.
git fetch
git branch -r

#: Prune: fetch, and delete the names whose branches are gone.
git fetch --prune

#: One branch is left besides main.
git branch -r
git log --oneline --graph --all -n 5

#: Three [deleted] lines, and easter-hours is still live.
wt answer pruned 3
wt answer live easter-hours
