#!/usr/bin/env bash
set -euo pipefail

#: You are standing in the middle of a merge. status says so.
git status

#: And the file has both versions in it, fenced off.
cat stock/aisle-b.md

#: This is not the moment. Undo the whole attempt in one command.
git merge --abort

#: No markers, no paused merge, main saying what it said before.
git status
cat stock/aisle-b.md
git log --oneline --graph --all
