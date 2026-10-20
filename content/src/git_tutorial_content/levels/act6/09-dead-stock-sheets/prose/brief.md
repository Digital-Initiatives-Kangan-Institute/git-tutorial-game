Pull, `git rm` both retired sheets, untrack the scratch file, push.

  git pull                                  two modify/delete conflicts
  git rm <path> <path>                      take both sheets off
  git rm --cached stocktake.tmp             untrack it, keep it on disk
  echo stocktake.tmp >> .gitignore          ignore it from now on
  git add .gitignore
  git commit --no-edit                      finish the merge
  git push

The retired sheets: `stock/aisle-e-overflow.md` and
`stock/seasonal-twine.md`. Afterwards `stocktake.tmp` should still be on
disk, and `git status` should not mention it.
