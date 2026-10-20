The scanner's log has filled up and rotated. There is now
`scanner.log`, `scanner.log.1` and `scanner.log.2`, and there will be
a `.3` at some point without anyone deciding it.

You ignored a directory on the scanner dumps job. A rule naming
`scanner.log` would be wrong by next week, and one naming all three
would be wrong the week after. The sign has to describe the kind of
file, not list the ones on the floor today.

`.gitignore` patterns can use `*`, which matches any run of
characters:

  *.log           every file ending in .log. Only one of these three
                  does: the rotated ones end in .log.1 and .log.2
  scanner.log*    every file starting with scanner.log

There is also a real new page, `docs/scanner.md`, which explains all
this and does belong in the records.

  try:  git status
        ls scanner.log*
        cat .gitignore

Write one pattern that covers all three logs, and commit it along with
the new page. As before: ignore them, do not delete them.
