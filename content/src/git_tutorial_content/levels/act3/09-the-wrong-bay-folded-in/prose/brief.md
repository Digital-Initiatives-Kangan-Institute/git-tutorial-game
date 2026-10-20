A merge is paused and it is the wrong branch. Abandon it, then merge
the right one.

  git status                 which branch is coming in
  git merge --abort          put everything back as it was
  git merge hotfix           the branch you meant
  git log --oneline --graph --all

`month-end` must still exist afterwards and must not be in `main`.
Theo needs it where it is.

If git asks for a merge message, `git merge --no-edit hotfix` accepts
the one it wrote.
