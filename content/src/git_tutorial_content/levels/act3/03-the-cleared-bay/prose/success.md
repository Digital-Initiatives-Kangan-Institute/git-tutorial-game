Both commits back, and you made nothing new to get them.

That is the sentence worth taking out of this act:

  deleting a branch deletes a name

The commits underneath were never touched. The same is true of the
thing that scares people more: `reset --hard` moves a branch label and
leaves the commits where they are. Either way the work goes quiet, not
away, and the reflog is what finds it.

There is a time limit, and it is generous. Unreachable commits are
cleared up eventually by git's own housekeeping, ninety days by default
for anything in the reflog. If you notice within an afternoon, which is
when people do notice, the work is there.

The one thing this cannot recover is work that was never committed. A
file you edited and never committed has no commit to point a name at.

Next job: undoing a commit on purpose.
