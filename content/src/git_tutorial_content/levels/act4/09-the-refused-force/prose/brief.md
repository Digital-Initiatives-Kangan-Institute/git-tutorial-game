Your rewritten commit will not push. Find out what forcing would have
cost, then send it up properly.

  git push                      rejected: not a fast-forward
  git push --force-with-lease   rejected: stale info
  git fetch                     go and see what changed
  git log --oneline --graph --all
  git merge --no-edit origin/stocktake-plan
  git push

Both commits must survive: Ines's log commit and your reworded draft.
Do not use plain `--force`.
