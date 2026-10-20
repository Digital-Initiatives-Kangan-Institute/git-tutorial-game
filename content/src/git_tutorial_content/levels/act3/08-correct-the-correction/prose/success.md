Four commits, and between them the whole story: the discount was
recorded, taken out, and put back.

That is what append-only history buys you. Nothing here rewrote
anything; two reverts, both additions, and the record matches what
happened in the office.

A thing people trip over: once a commit has been reverted, re-applying
it is *not* done by merging the branch it came from again. Git sees
those commits as already in the history, because they are, and does
nothing. Reverting the revert is the way back.

You now have the full set:

  restore   a file you have changed but not committed
  reset     a commit nobody else has seen
  revert    a commit that has left your machine

Before that, one more kind of mistake: merging the wrong branch.
