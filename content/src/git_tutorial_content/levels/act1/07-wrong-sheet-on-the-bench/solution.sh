#!/usr/bin/env bash
set -euo pipefail

#: One file, and it appears in both lists at once.
git status

#: The second edit, on disk.
git diff

#: The first edit, already staged. Different text.
git diff --staged

#: Unstage first: the commit's version overwrites the staged one.
git restore --staged docs/receiving.md

#: Now the file on disk. Doing this first would have copied the bad
#: staged version down onto it.
git restore docs/receiving.md

#: Back to what the last commit says.
cat docs/receiving.md
git status
