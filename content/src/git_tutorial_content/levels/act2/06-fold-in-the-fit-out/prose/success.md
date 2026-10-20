One line again, and both names on the same commit.

Look at what did not happen: there is no extra commit recording the
merge. Git had nothing to combine, because your two commits already
sat directly on top of `main`, so it moved the name and stopped. That
is the whole of a fast-forward.

  git log --oneline --graph --all

This is the *easy* case, and it only happened because `main` stood
still. The moment somebody else commits to `main` while your branch is
open, the two lines have genuinely diverged and no name can simply
move to fix it. That shape makes a merge commit, and it is the next job.
