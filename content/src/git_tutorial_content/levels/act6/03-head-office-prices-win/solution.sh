#!/usr/bin/env bash
set -euo pipefail

#: Your pencilled prices are committed. Pull Head Office's list.
git pull --no-edit || true
git status

#: Only the price list is held. The dispatch log merged on its own.
git log --merge --oneline

#: Head Office's prices stand: take their version of this one file, whole.
git restore --theirs suppliers/price-list.md
cat suppliers/price-list.md

#: Nothing differs from Head Office's copy.
git diff origin/main -- suppliers/price-list.md

#: restore --theirs does not settle the file. add does.
git add suppliers/price-list.md
git commit --no-edit

#: Your log line is still there.
grep Kestrelby dispatch/log.md
git push
git log --oneline --graph -n 4
