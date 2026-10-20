#!/usr/bin/env bash
set -euo pipefail

#: Which branch are you on? The first line of git status says so.
git status

#: Every commit, one line each, newest first. Count them.
git log --oneline

#: The second commit ever made is the second line from the bottom.
git log --oneline | tail -2

#: Plain git log shows the author, which --oneline leaves out.
git log -1

#: The answers, typed the way the job sheet's boxes would take them.
wt answer branch main
wt answer count "$(git rev-list --count HEAD)"
wt answer second "$(git rev-list --reverse HEAD | sed -n 2p | cut -c1-7)"
wt answer author "$(git log -1 --format=%an | cut -d' ' -f1)"
