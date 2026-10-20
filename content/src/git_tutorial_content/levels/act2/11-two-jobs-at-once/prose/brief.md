Fix `compare with the delivary note` to `compare with the delivery
note` in `docs/receiving.md`, on a branch called `typo-fix`. Then get
back to what you were doing.

  git stash / git stash pop   put the pending work aside and back
  git switch main             the fix branch starts from main
  git switch -c typo-fix      make it and move onto it

At the end: `typo-fix` has the correction committed, `main` has
nothing new on it, you are on `stocktake-prep`, your unfinished page
is back in front of you, and the stash is empty.

Branch from `main`, not from `stocktake-prep`. Your pending page is in
the stash and belongs to no branch, but `stocktake-prep` has a commit
on it, and a fix branch cut from there would carry that commit along
with the fix.
