#!/usr/bin/env bash
set -euo pipefail

#: Four untracked files. Three of them are the same thing, numbered.
git status

#: And there will be a scanner.log.3 next week.
ls scanner.log*

#: So the rule has to be a pattern, not a list of names.
printf 'scanner.log*\n' >> .gitignore  # >> appends; > would overwrite

#: Quiet about all three, still reporting the new page.
git status

#: Commit the rule and the page together.
git add .gitignore docs/scanner.md
git commit -m "Ignore rotated scanner logs"

#: Your commits, on top of the warehouse's history.
git log --oneline
