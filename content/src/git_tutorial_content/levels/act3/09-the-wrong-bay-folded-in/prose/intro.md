Incident report from Theo: you wanted the cartons fix on `main` before
the end of the day. It is on a branch called `hotfix`. You typed a
merge, and git stopped with a conflict in `dispatch/log.md`.

The instinct is to open the file and start choosing between the two
versions. Read `git status` first.

The branch coming in is `month-end`. That is Theo's job bay, the one
that closes the month, and it is not meant to land until the stocktake
is actually done. The conflict is not the problem. The conflict is the
first thing that made you look at what you typed.

Nothing has been merged yet. A conflicted merge is a *paused*
operation: `main` still points where it always did, the merge commit
has not been made, and everything so far has happened in your working
tree and staging area. The crate is held at inspection, not on the
shelf line.

So there is nothing to undo. There is something to *abandon*.

    git merge --abort

You met this in Act 2 as the way out of a merge you were unsure about.
This is the most common case of all: the merge was simply the wrong
command, and the way out is the same.

Then do what you meant to do. `hotfix` touches
`suppliers/price-list.md`, which nothing on `main` has touched, so git
will combine it without asking you anything.

  try:  git status
        git log --oneline --graph --all

The cartons fix merged into `main`, `month-end` left alone, no paused merge.
