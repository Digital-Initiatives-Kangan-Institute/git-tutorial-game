Two changes are pending and neither is committed. Undo both, so the
working tree matches the last commit again.

One change is staged. One is not. That matters:

  the last commit         what is recorded
  the staging area        what is staged next
  the working tree        the file on disk right now

  git restore --staged <path>   commit -> staging area
  git restore <path>            staging area -> working tree

A change only on disk needs one command. A staged change needs both,
in that order. Do not commit your way out of this.
