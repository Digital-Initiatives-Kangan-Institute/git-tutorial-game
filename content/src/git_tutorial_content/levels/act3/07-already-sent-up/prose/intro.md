Incident report from Theo: Ines rang from Head Office to ask why pallet
wrap is down to 2.40 a roll. It is not. Kestrelby still charge 4.20.
On Friday you read the price off the wrong line of their quote and
committed it as "Update the pallet wrap price".

It needs to come out. Two things make that different from everything
you have done in this act so far.

The first is in the log: you made two more commits after it, the B-15
count and its line in the dispatch log, and both are good. Moving `main`
back far enough to lose the bad one loses those too.

The second is Ines. Head Office has the commit. Their copy holds it by
hash, and every later hash is built on it. `reset` would rewrite the
line of commits so that their version and yours disagree about what
happened, and the next time anyone combines them, git has a genuine
mess to sort out.

So: do not change the past. Add to it.

    git revert <hash>

*Revert* looks at what one commit changed, works out the opposite, and
makes a *new commit* containing that: a correction note, booked in like
any other crate. The bad commit stays in the history where it is. On
top sits the commit that undoes it, and the files end up as though it
had never happened.

This job is graded on the route, not only the result. `reset` would get
nearly the right files, and it will not be accepted.

  try:  git log --oneline
        git show --stat HEAD~2

The wrong price gone, the two later commits untouched, the undo its own commit.
