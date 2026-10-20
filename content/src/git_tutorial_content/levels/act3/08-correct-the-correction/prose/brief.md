The commit that removed the bulk discount is the newest one. Undo it.

  git log --oneline               find the Revert commit
  git show <hash>                 see what it took out
  git revert --no-edit <hash>     put it back, as a commit
  cat suppliers/price-list.md

Do not retype the discount by hand. The repository already has it.
