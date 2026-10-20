Marta has signed off the March stocktake. The figure she signed is
Theo's aisle B count, the commit called "Count aisle B", and she wants
it sealed so that in six months nobody has to ask which version it was.

A branch is no good for this. A branch is a label that moves: every
commit on it carries the label forward. What Marta wants is a label
that stays exactly where it is put.

That is a *tag*: a fixed name for one commit. A seal on one crate.

    git tag stocktake-march           tag HEAD, the commit you are on
    git tag stocktake-march <hash>    tag the commit you name

"Count aisle B" is not your newest commit any more, so name it.

Tags are not sent up with an ordinary `git push`. You send one by name:

    git push origin stocktake-march

  try:  git log --oneline
        git tag
        git log --oneline --decorate

Seal Theo's count, then send the seal to Head Office.
