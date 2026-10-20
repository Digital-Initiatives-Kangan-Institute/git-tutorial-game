Push refused, then a stale name. Fix both.

  git push                  read the refusal
  git pull --no-edit        Theo's commit, merged with yours
  git push                  accepted
  git branch -r             origin/april-slots is still listed
  git fetch --prune         remove it
  git log --oneline --graph --all -n 5

No `--force`. Theo's commit has to stay at Head Office.
