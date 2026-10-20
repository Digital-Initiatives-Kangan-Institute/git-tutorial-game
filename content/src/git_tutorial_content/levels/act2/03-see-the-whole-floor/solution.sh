#!/usr/bin/env bash
set -euo pipefail

#: One branch at a time tells you nothing about the other.
git log --oneline

#: Both at once, with the shape drawn down the left.
git log --graph --all --oneline

#: Count each side directly, to check what the drawing told you.
git log --oneline main..aisle-d-fitout
git log --oneline aisle-d-fitout..main

#: The commit where the two lines join is the one they still agree on.
git merge-base main aisle-d-fitout

#: The answers, typed the way the job sheet's boxes would take them.
wt answer ahead "$(git rev-list --count main..aisle-d-fitout)"
wt answer behind "$(git rev-list --count aisle-d-fitout..main)"
wt answer base "$(git rev-parse --short "$(git merge-base main aisle-d-fitout)")"
