Pull, settle the conflict on B-14, push.

  git pull               fetch Theo's commit and merge; it stops
  git status             the conflicted file, under "Unmerged paths"
  git add <path>         this file is settled
  git commit --no-edit   finish the merge
  git push               send it up
  git merge --abort      start again, any time before the commit

Edit `stock/aisle-b.md` so the B-14 block reads exactly:

    38 rolls counted for the stocktake.

Delete every `<<<<<<<`, `=======` and `>>>>>>>` line. Do not reach for
`--force`: Theo's commit has to stay at Head Office.
