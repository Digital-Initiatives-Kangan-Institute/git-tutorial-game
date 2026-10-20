#!/usr/bin/env bash
set -euo pipefail

#: Two branches now, and the page is here because you are on aisle-d-fitout.
git branch
ls docs

#: Move to main. Watch what happens to the folder.
git switch main

#: The page is gone from disk: it was never committed on this branch.
git status
ls docs

#: It is not lost. It is on the other branch, exactly where you left it.
git log --oneline aisle-d-fitout

#: Prove it by going back, then return to main to finish.
git switch aisle-d-fitout
ls docs
git switch main
