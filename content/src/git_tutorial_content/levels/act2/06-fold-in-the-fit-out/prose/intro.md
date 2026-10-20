The aisle D fit-out page is finished, in its own bay, and `main` has
not moved since that bay opened. Time to fold the work back in.

  git merge <name>

Merging has a direction, and getting it the wrong way round is the
most common first mistake. You stand on the branch that should
*receive* the work, and you name the branch the work is *on*. So to
get the fit-out into `main`, you switch to `main` first, then merge
`aisle-d-fitout`.

What happens next depends on the shape. Right now `main` has no
commits of its own since the branch parted, so there is nothing to
reconcile: every commit on the bay sits directly on top of where
`main` is. Git does not invent a commit for that. It just moves the
`main` name forward to where your branch already is.

That is a *fast-forward*. Afterwards the history is still one straight
line: no merge commit, nothing combined, the name caught up.

  try:  git log --oneline --graph --all
        git status
        git branch

Finish on `main`, pointing at the same commit as `aisle-d-fitout`,
with no merge commit in the history.
