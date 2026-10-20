`main` has both Theo's dispatch entry and your racking checklist, and
on top of them a commit with two parents.

  git log -1 --pretty='%h %p %s'

Two hashes in the middle: that is the merge commit naming both sides.
Every other commit in these records has one parent.

There are two kinds of merge and you have now done both:

  fast-forward   main had not moved; the name slid forward, no commit
  merge commit   both had moved; a new commit joined the two lines

You do not choose between them. Git picks from the shape, and the
shape depends on whether anyone committed to `main` while you were
away. `git log --graph --all` before you merge tells you which you are
about to get.

Both merges so far combined themselves. Soon you meet one that cannot.
