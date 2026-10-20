#!/usr/bin/env bash
set -euo pipefail

#: One commit of your own, and no sign yet that anything else happened.
git log --oneline --graph --all
git status

#: Read Head Office's bulletin, and take in what it says.
git pull --no-edit

#: A merge commit at the top that you never typed a message for.
git log --oneline --graph --all

#: Both sides are in: her section, and your log line.
git status
