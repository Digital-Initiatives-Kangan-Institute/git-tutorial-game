#!/usr/bin/env bash
set -euo pipefail

#: Theo left a change on the shared terminal. Read it before booking it.
git status
git diff

#: Book the recount on main and send it up.
git add stock/aisle-b.md
git commit -m "Recount B-14 pallet wrap"
git push

#: HEAD is the recount commit now, so the tag needs no hash.
git tag recount-b14
git log --oneline --decorate -n 2

#: The branch push did not take the tag. Send it by name.
git push origin recount-b14
git ls-remote --tags origin
git status
