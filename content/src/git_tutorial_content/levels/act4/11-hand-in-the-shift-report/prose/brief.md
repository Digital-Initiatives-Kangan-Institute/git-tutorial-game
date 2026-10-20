Hand in your shift report by pushing it.

  git switch -c shift-report
  (add a `scratch.txt` line to the end of `.gitignore`)
  (write `shift-report.md`, starting with `# Shift report`)
  git status                  scratch.txt is no longer listed
  git add .gitignore shift-report.md
  git commit -m "Hand in my shift report"
  git push -u origin shift-report

Leave the comment at the top of `.gitignore` alone: add a line, do not
replace the file.
