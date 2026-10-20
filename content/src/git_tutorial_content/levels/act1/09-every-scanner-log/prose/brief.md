Four files are untracked. `docs/scanner.md` belongs in the records;
the three logs do not, and neither do the ones the scanner has not
written yet.

`.gitignore` patterns can use `*`, which matches any run of
characters:

  *.log          every file ending in .log, which the rotated
                 ones do not, so this misses two of the three
  scanner.log*   every file starting with scanner.log

Add one pattern that covers all three, then commit it along with the
new page. Ignore the logs, do not delete them.
