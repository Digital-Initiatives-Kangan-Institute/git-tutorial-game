`main` is three commits short. Put it back.

  git reflog                      where main was before the reset
  git log --oneline ORIG_HEAD     what git saved for you
  git reset --hard ORIG_HEAD      move main back there, files included
  git log --oneline --graph --all

Either route is fine: `ORIG_HEAD` or the hash from the reflog. What
matters is that `main` ends up pointing at the commit it pointed at
before the reset, with the working tree to match.

`--hard` is the right flag this time: you want the files back too.
