#!/usr/bin/env bash
set -euo pipefail

#: Two commits on this branch, none on main since it started.
git log --oneline --graph --all

#: Merging goes into the branch you are standing on, so move first.
git switch main

#: Bring the work in. Name the branch you want, not the one you are on.
git merge aisle-d-fitout

#: One line again. main did not gain a merge commit: its name moved.
git log --oneline --graph --all
git status
