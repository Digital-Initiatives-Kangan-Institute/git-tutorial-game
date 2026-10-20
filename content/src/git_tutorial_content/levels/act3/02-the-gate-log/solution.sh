#!/usr/bin/env bash
set -euo pipefail

#: The ordinary log cannot see it. Ten commits yesterday, nine today.
git log --oneline

#: The reflog can: every position HEAD has held, newest first.
git reflog -n 10

#: The top line is the reset. The line below it is where main was.
git reflog -n 2

#: Both answers, typed the way the job sheet takes them.
wt answer before_reset "$(git rev-parse --short 'HEAD@{1}')"
wt answer operation reset

#: Nothing has been recovered yet. That is the next job.
git status
