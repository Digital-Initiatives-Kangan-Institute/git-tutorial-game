#!/usr/bin/env bash
set -euo pipefail

#: This folder has known where it came from since the day it was made.
git remote -v

#: Make the copy a new starter would get, next to this one.
rm -rf ../new-starter
git clone "$(git remote get-url origin)" ../new-starter

#: A clone is the whole history, not a snapshot of the latest version.
git -C ../new-starter log --oneline

#: The answers, typed the way the job sheet's boxes would take them.
wt answer remote_name origin
wt answer fresh_commits "$(git -C ../new-starter rev-list --count main)"

#: The copy has done its job; nothing later needs it.
rm -rf ../new-starter
