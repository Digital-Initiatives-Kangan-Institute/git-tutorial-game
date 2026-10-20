Ines has sent something up. Read it without taking it.

  git fetch                         collect what the remote has
  git status                        how far behind you now are
  git log --oneline origin/main     what is waiting
  git log --oneline --graph --all   both lines at once

Afterwards `main` must be one commit behind `origin/main`, with Ines's
commit visible but not merged. Do not run `git pull` here; that is the
job after next.
