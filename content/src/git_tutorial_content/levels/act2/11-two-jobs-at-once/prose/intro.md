You are part way through a sentence in the stocktake plan, on
`stocktake-prep`, and a second job arrives: somebody has spotted a
typo in the receiving procedure. "delivary note".

Nothing here is new. What is new is that the urgent job follows the
same rule as every other job: it does not go straight onto `main`. It
needs a branch of its own, and that branch has to start from `main`,
not from the half-finished work you are standing in.

So there are three moves, and the order is the whole lesson:

  1  put the pending work aside, so you are allowed to leave
  2  go to main, and branch from there
  3  come back and take the work out again

Step two is the one to slow down on. `git switch -c` makes the new
branch *at the commit you are standing on*. Made from `stocktake-prep`,
the fix branch would start on top of that branch's commit, and the two
jobs would arrive together whenever anybody merged it. Go to `main`
first and the fix branch carries only the fix.

  try:  git status
        git branch
        git log --oneline --graph --all

Finish with a `typo-fix` branch carrying the corrected procedure,
`main` with nothing new on it, and you back on `stocktake-prep` with
your unfinished page in front of you and an empty stash.
