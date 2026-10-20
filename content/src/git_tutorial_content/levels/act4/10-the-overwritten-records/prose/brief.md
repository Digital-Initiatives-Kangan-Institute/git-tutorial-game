You force-pushed over a colleague's commit. Put it back.

  git log --oneline origin/stocktake-plan   what Head Office has now
  git reflog show origin/stocktake-plan     where it has been
  git log --oneline <hash>                  check you have the right one
  git merge --no-edit <hash>                bring her commit into yours
  git push

Her commit must come back as *her* commit: same hash, her name on it.
Retyping the log change would leave her authorship off the history.
