#!/usr/bin/env bash
set -euo pipefail

#: The commit holds the README link and a file nobody should see.
git show --stat HEAD

#: Move the label back and unstage everything. Files on disk untouched.
git reset HEAD~1

#: README.md is modified; scratch.md is untracked again.
git status

#: Stage only what belongs in the history.
git add README.md
git diff --staged

#: Commit the one thing, and leave the notes where they were.
git commit -m "Link the dispatch log"
git status
git show --stat HEAD
