#!/usr/bin/env bash
set -euo pipefail

#: One branch so far. The * marks the one you are on.
git branch

#: Make a branch for the fit-out and move onto it, in one command.
git switch -c aisle-d-fitout

#: Same files, same history. You are only standing somewhere else.
git status
git log --oneline
