#!/usr/bin/env bash
set -euo pipefail

#: Three files pending, and only one of them is finished.
git status

#: What is staged is the aisle B draft: the one that is NOT ready.
git diff --staged

#: Unstage it. The draft text is untouched; it just will not be committed.
git restore --staged stock/aisle-b.md

#: The README has a keyboard slip in it. That one goes.
git restore README.md

#: Now stage the only finished thing.
git add dispatch/log.md

#: Check what is about to be recorded. One line, the right one.
git diff --staged

#: Record it.
git commit -m "Note the opening checks in the dispatch log"

#: The aisle B draft is still pending, still Theo's to finish.
git status
