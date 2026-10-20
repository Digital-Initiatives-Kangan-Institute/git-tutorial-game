#!/usr/bin/env bash
set -euo pipefail

#: The first line of status is the whole diagnosis.
git status

#: The commit you are standing on is the top one here.
git log --oneline

#: Note that hash on the job sheet, the way you would type it.
wt answer detached_at "$(git rev-parse --short HEAD)"

#: Now go back. A branch is under you again, and the files are today's.
git switch main
git status
