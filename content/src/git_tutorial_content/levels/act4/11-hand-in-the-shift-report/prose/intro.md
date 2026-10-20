One thing left: Marta wants your shift report for the week.

Your rough notes are already in `scratch.txt`. They were useful for
writing the report, and they are not the report. Nobody at Head Office
needs to read "recount before telling Ines".

Keeping a file out of the records is *a line in a file*. You have
done it before: add the name to `.gitignore` and git stops mentioning
it. Nothing is deleted. The notes stay on your disk, and `git add .`
can no longer sweep them up by accident.

Then the report itself: write it in `shift-report.md`, and hand it in
the way work is handed in from now on. Not as an attachment. Pushed.

Put it on a branch of its own rather than on `main`. `main` is the
warehouse's records; your report is for Marta to read and decide
about. A branch with your work on it, pushed to Head Office, is how
most work gets submitted for review.

  try:  git status
        cat .gitignore
        git switch -c shift-report

Hand in a `shift-report` branch holding the report and the
`.gitignore` that keeps your notes out of it.
