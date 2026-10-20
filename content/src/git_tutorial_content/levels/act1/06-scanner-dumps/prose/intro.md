The handheld scanners dump a file every time someone runs an export,
and they dump it straight into the records folder. Theo is tired of
`git status` listing them.

Most projects have files like this: tool output, logs, temporary
files, downloaded dependencies. They are produced by machines, they
change constantly, and nobody needs them in the history.

A *.gitignore* file lists paths git should stop reporting. Think of
it as a sign telling the stock checker what to walk past. This
repository already has one at the top, holding only comments so far.

Patterns can name a file, a kind of file, or a whole directory:

  scanner.log      one file
  *.tmp            every file ending in .tmp
  scanner-export/  a directory, and everything in it

One catch, and it catches everyone once: ignoring only works on files
git is not already tracking. Ignore things before you commit them.

Right now the scanner has written three files in `scanner-export/`,
and there is also one real new page, `docs/opening-checks.md`.

  try:  git status
        cat .gitignore

Ignore the export directory, and commit `.gitignore` together with
the new page. Do not delete anything.
