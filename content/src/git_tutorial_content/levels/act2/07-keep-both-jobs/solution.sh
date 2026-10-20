#!/usr/bin/env bash
set -euo pipefail

#: Two lines, both with commits on them. Nothing can just slide forward.
git log --oneline --graph --all

#: Same direction as before: stand on the receiver, name the source.
git switch main

#: --no-edit accepts the message git writes, instead of opening an editor.
git merge racking-checks --no-edit

#: A new commit with two parents, and both sides' work underneath it.
git log --oneline --graph --all
git log -1 --pretty='%h %p %s'
ls docs
git status
