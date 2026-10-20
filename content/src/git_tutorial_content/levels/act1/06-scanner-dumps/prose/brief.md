Four files are untracked. One belongs in the records; three are
scanner output.

  docs/opening-checks.md   a real page: commit it
  scanner-export/*.csv     generated: ignore it

`.gitignore` already exists. Add a pattern for the export directory,
then commit it along with the new page. Both have to end up in the
history.

  scanner-export/   a trailing slash means the whole directory

Do not delete the export files. The goal is a quiet `git status`, not
an empty disk.
