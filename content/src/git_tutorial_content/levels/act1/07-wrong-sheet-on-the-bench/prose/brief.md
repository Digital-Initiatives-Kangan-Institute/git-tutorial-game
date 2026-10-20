`docs/receiving.md` has been changed twice: once staged, once not.
Undo both, so the file reads the way the last commit has it.

  git diff           the second edit, on disk
  git diff --staged  the first edit, staged

Both are unwanted and both must go. Order matters:

  git restore --staged <path>   commit -> staging area
  git restore <path>            staging area -> working tree

If you restore the file on disk first, you copy the staging area onto
it, and the staging area still holds the first unwanted edit.
