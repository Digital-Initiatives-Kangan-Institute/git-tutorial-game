#!/usr/bin/env bash
set -euo pipefail

#: Four untracked files. Only one of them belongs in the records.
git status

#: These three were written by the scanner's export.
head -1 scanner-export/aisle-b.csv

#: A whole directory, so the pattern ends in a slash.
printf '\nscanner-export/\n' >> .gitignore  # >> appends; a single > would overwrite

#: Status goes quiet about scanner-export/, and still reports the new page.
git status

#: Commit the rule and the page together.
git add .gitignore docs/opening-checks.md
git commit -m "Ignore the scanner exports"

#: Still on disk. Ignoring is not deleting.
ls scanner-export/
