Prune the stale name, pull `main`, and find out who merged Theo's
branch.

  git branch -r                  your notes of Head Office's branches
  git fetch --prune              update them, remove the deleted ones
  git pull                       bring main up to date
  git log --oneline --graph -n 4 the merge, with Theo's commit inside
  git log -1                     the merge commit's author

A plain `git pull` brings the merge but leaves the stale name behind.
