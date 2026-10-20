#!/usr/bin/env bash
set -euo pipefail

#: What this repository currently believes about Head Office.
git remote -v
git log --oneline --graph --all

#: Go and ask. This changes no branch of yours and no file on disk.
git fetch

#: Now it knows: one commit of Ines's, under a name of its own.
git status
git log --oneline origin/main
git log --oneline --graph --all

#: And your own main is exactly where you left it.
git log --oneline -n 1 main
