Undo one commit that is three down, without touching the two above it.

  git log --oneline                find the price commit's hash
  git show --stat <hash>           check it is the right one
  git revert --no-edit <hash>      commit the opposite of it
  git log --oneline

`--no-edit` keeps the message git writes (`Revert "..."`). Without it
an editor opens.

`reset` is refused here. Some undos have to be additions.
