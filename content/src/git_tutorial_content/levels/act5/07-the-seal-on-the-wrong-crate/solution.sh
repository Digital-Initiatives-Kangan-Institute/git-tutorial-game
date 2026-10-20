#!/usr/bin/env bash
set -euo pipefail

#: The tag is on HEAD, Ines's April prices. Marta wanted the week's log.
git log --oneline --decorate -n 4

#: Not at Head Office yet, so fixing it here is the whole fix.
git ls-remote --tags origin

#: A tag does not move. Delete it, and make it again in the right place.
git tag -d dispatch-21-march
week=$(git log --format=%h --grep="^Log the week's dispatches$" -n 1)
git tag dispatch-21-march "$week"
git log --oneline --decorate -n 4

#: Now send it up.
git push origin dispatch-21-march
git ls-remote --tags origin
git status
