Your push is rejected because Head Office has a commit you do not.

  git push                  read the rejection
  git pull --no-edit        fetch Ines's commit and merge it
  git log --oneline --graph --all
  git push                  accepted

End with `main` and `origin/main` at the same commit, and both commits
on Head Office's `main`. Do not reach for `--force`; it is the wrong
answer to this.
