Pull, read the conflict before fixing it, then resolve and push.

  git pull                       it stops
  git status                     the conflicted files
  grep -c '^<<<<<<<' <file>      blocks in a file
  git log --merge --oneline      the commits on both sides that disagree
  git add <path> ...             each settled file
  git commit --no-edit           finish the merge
  git push

Answer before you resolve: an added file drops out of `git status`'s
"Unmerged paths" and out of `git log --merge`.

How it should end:

    stock/aisle-b.md          39 rolls counted for the stocktake.   (yours)
    suppliers/price-list.md   price = 4.45, hold until 30 June      (Head Office's)
