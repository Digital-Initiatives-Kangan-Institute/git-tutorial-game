#!/usr/bin/env bash
set -euo pipefail

#: You are on peak-rota. A branch cannot be deleted while you stand on it.
git status
git switch main

#: Before deleting anything, see the merge with your own eyes.
git pull
git log --oneline --graph --all -n 6

#: Now its work is in main, so -d agrees. The commits stay; the name goes.
git branch -d peak-rota

#: Head Office's copy is a separate branch. Ask Head Office to delete it.
git push origin --delete peak-rota
git branch -a
git status
