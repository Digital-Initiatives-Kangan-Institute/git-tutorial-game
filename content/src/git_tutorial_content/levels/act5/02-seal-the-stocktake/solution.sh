#!/usr/bin/env bash
set -euo pipefail

#: The count Marta signed off is not the newest commit. Find it.
git log --oneline

#: Its hash, looked up by its message rather than copied by eye.
count=$(git log --format=%h --grep='^Count aisle B$' -n 1)

#: Tag that commit, not HEAD.
git tag stocktake-march "$count"
git log --oneline --decorate -n 4

#: A tag stays local until it is pushed by name.
git push origin stocktake-march
git ls-remote --tags origin
git status
