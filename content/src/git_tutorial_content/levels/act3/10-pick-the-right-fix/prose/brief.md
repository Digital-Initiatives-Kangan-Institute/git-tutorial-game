Three messes, three different undos. Work out which is which before you
type.

  git status            what is uncommitted
  git log --oneline     what is committed, and in what order

  git restore <path>                 a file you have not committed
  git reset --hard HEAD~1            the newest commit, yours alone
  git revert --no-edit <hash>        a commit other people have

Ending state:

  stock/aisle-b.md matches its last commit
  no WIP commit anywhere in the history of main
  the wrong price gone, its commit still in the log
  three commits on top of where main started, nothing pending
