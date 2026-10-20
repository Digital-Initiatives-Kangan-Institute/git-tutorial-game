#!/usr/bin/env bash
set -euo pipefail

#: A branch to hand in on, so main stays as the warehouse's records.
git switch -c shift-report

#: git mentions your rough notes, because nothing tells it not to.
git status
cat .gitignore

#: One line keeps them out of everything you hand in.
echo "scratch.txt" >> .gitignore

#: Write the notes up as the report.
cat > shift-report.md <<'MD'
# Shift report

Week ending 28 March. Trainee, Tallowmere Distribution.

- Read the records and found out where they come from.
- Sent work up to Head Office, and took its updates in.
- Put back a commit I had forced over, from the reflog.
MD

#: The report and .gitignore are listed; scratch.txt is not.
git status

git add .gitignore shift-report.md
git commit -m "Hand in my shift report"

#: Handing in is pushing. Nothing is attached to anything.
git push -u origin shift-report
git status
