#!/usr/bin/env bash
set -euo pipefail

#: Two files changed. Status says which, not what.
git status

#: What is NOT staged: the aisle B edit.
git diff

#: What IS staged: the dispatch log line. The two never overlap.
git diff --staged

#: Committing records what is staged and nothing else, so no git add.
git commit -m "Note the safety sheet in the dispatch log"

#: The aisle B edit is still there, still unstaged.
git status
