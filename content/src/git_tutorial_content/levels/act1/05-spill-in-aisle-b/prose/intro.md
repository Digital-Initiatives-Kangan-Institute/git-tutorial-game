Someone has made a mess of two sheets and walked off. Neither change
is wanted, and neither has been booked in. That also means git has no
copy to give back: `git restore` is the one command in this act that
destroys work for good. That is what you want here, but know it before
you type it.

Cleaning up needs the three copies of every file to be clear:

  the last commit         what is recorded
  the staging area        what is staged for the next commit
  the working tree        the file as it is on disk right now

Two commands move a copy from one place to the next:

  git restore --staged <path>   commit -> staging area
  git restore <path>            staging area -> working tree

*git restore --staged* takes a change off the packing bench and puts
it back on the floor. *git restore* sweeps the floor back to what the
bench holds. So a change that was never staged needs one command. A
change that IS staged exists in two places and needs both, in that
order.

  try:  git status
        git diff
        git diff --staged

Undo both changes, leaving a clean working tree with the history
exactly where it already is. Do not commit.
