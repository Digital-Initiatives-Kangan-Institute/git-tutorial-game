#!/usr/bin/env bash
set -euo pipefail

#: One branch, nothing pending.
git status
git branch

#: Branch first, by habit. What matters is being here when you commit.
git switch -c racking-checks

#: Write the page. You would do this in your editor.
cat > docs/racking-checks.md <<'PAGE'
# Racking checks

Walk every aisle on Monday morning, before the first delivery.

    bent upright     tape the bay off and tell Marta
    missing pin      refit it before anything is loaded
PAGE

#: The cycle from Act 1, unchanged: look, stage, commit.
git status
git add docs/racking-checks.md
git commit -m "Add the weekly racking checks"

#: Your commit is on racking-checks. main is where it was.
git log --oneline --graph --all
