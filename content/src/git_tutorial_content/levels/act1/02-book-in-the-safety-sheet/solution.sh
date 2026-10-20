#!/usr/bin/env bash
set -euo pipefail

#: The sheet is on disk. Git has never seen it, so it is "untracked".
git status

#: Stage it: mark it to go into the next commit.
git add docs/safety.md

#: Same command, different answer. The file has moved between lists.
git status

#: Record everything staged as one commit.
git commit -m "Add the safety sheet"

#: Your commit is now at the top of the history.
git log --oneline

#: And the phrase worth recognising: nothing to commit, working tree clean.
git status
