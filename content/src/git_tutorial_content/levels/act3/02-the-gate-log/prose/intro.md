Incident report from Marta: she ran `git log --oneline` this morning
and the top commit is "Start the dispatch note for 3 March". The one
above it, Theo's "Log the week's dispatches", is not there.

Nine commits. There were ten yesterday.

Nothing you can do with `git log` will find it, and that is not `log`
being unhelpful. `git log` walks backwards from a branch, so it can only
show you commits something still points at. Yesterday's tip is not one
of those any more. It is a crate out in the yard: still sealed, still
whole, just not on any shelf line.

Git keeps a second record for exactly this. Every time HEAD moves (every
commit, switch, merge, reset) git appends a line saying where it went
and what moved it. That record is the *reflog*, and it is the gate log
of this warehouse: every move the forklift has made.

    git reflog

Newest first, one line per move:

    <hash> HEAD@{0}: reset: moving to HEAD~1
    <hash> HEAD@{1}: (the move before that)

Read it as a history of *you*, not of the records. The hash at the start
of each line is where HEAD landed after that move. So the line below a
mistake is where you were standing before it.

This job only asks you to read. Nothing is recovered yet.

  try:  git log --oneline
        git reflog

Find where main was before the reset, and what the reflog calls the move.
