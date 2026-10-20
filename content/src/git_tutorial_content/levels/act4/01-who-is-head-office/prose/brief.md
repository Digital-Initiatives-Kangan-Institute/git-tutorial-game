Read where this repository came from, then make a second copy and
count what is in it.

  git remote -v                         the remotes, with addresses
  git remote get-url origin             just the address
  git clone <address> ../new-starter    a second copy, next to this one
  git -C ../new-starter log --oneline   look inside it without going there

`git -C <folder>` runs a command as though you were in that folder.
Delete `../new-starter` when you are done; nothing later needs it.
