No new commands. A harder shape for the two you learned on the spill.

Someone added a note to the receiving procedure saying the BOOK-IN
scanner is "probably faulty", put the sheet on the packing bench, then
went back and added that it is "definitely faulty". Ines has checked:
the scanner is fine. Neither note should exist.

So `docs/receiving.md` has been changed, staged, then changed again,
and all three copies are now different:

  the last commit         the original procedure
  the staging area        the first note
  the working tree        the first note plus the second

`git restore <path>` copies from the staging area, not from the last
commit. Undoing the file on disk first would not give you the original
back: it would give you the first note, and throw the second away.

  try:  git status
        git diff
        git diff --staged

Get the file back to what the last commit says, with nothing staged
and nothing pending. Order matters.
