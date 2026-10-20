One commit holds two things. Keep one, drop the other.

  git reset HEAD~1      un-commit and unstage (--mixed is the default)
  git status            README.md modified, scratch.md untracked
  git add README.md     stage only what belongs
  git diff --staged     read it before committing this time
  git commit -m "Link the dispatch log"

`scratch.md` should end up untracked and still on disk. Do not delete
it: the point is that it never belonged in the commit, not that it
should not exist.
