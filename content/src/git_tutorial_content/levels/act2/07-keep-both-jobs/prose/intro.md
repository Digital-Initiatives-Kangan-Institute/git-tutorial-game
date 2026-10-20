Same command as last job, different shape, and this is the one that
confuses people.

While your racking checklist sat in its bay, Theo logged the Fennick
dispatch on `main`. Both lines have moved since they parted. There is
no longer a version of "move the name forward" that works: `main` has
a commit your branch has never seen, and your branch has a commit
`main` has never seen.

Git cannot fix that by moving a name, so it does the other thing. It
takes the two lines and makes a new commit whose job is to join them.
That is a *merge commit*, and it is the only kind with more than one
parent: here two, one on each side of the join.

This answers a question that bothers people for months: "why is there
a commit I did not write, saying Merge branch something." You did make
it. It appeared because the two histories genuinely diverged, and a
commit with two parents is how git records that they came back
together.

Nothing here conflicts. Git combines the two sides line by line, and
asks for help only where both sides changed the same lines. Two people
editing different places, even in the same file, merge without a
murmur.

  try:  git log --oneline --graph --all
        git log --oneline main..racking-checks
        git log --oneline racking-checks..main

Finish on `main`, carrying both jobs, with a merge commit on top.
