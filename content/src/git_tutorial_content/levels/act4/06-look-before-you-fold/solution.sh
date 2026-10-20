#!/usr/bin/env bash
set -euo pipefail

#: Read the bulletin, without taking anything yet.
git fetch
git status

#: What is waiting, and what it touches.
git log --oneline main..origin/main
git diff --stat main origin/main

#: One of those files is the one you committed this morning.
git diff main origin/main -- stock/aisle-b.md

#: The answers.
wt answer waiting "$(git rev-list --count main..origin/main)"
wt answer touched stock/aisle-b.md

#: Different ends of the file, so this combines without asking.
git merge --no-edit origin/main
git log --oneline --graph --all
