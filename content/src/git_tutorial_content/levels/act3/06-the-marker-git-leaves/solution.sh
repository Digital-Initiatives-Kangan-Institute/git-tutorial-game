#!/usr/bin/env bash
set -euo pipefail

#: Three commits gone from the log, and the files with them.
git log --oneline
git status

#: Not gone: the reflog has every position HEAD held this morning.
git reflog -n 10

#: And git wrote down where you were before the reset, under a name.
git log --oneline -n 1 ORIG_HEAD

#: Move main back to it. --hard, so the files come back too.
git reset --hard ORIG_HEAD

#: Three commits, the files restored, and no merge to show for it.
git log --oneline --graph --all
git status
