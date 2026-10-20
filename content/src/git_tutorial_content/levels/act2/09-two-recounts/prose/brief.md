Merge `recount-b14` into `main`. The same line changed on both sides,
so git will stop and ask you to decide.

  git merge recount-b14   start it
  git status              which file is unresolved, and the ways out
  git add <path>          this one is settled
  git commit --no-edit    finish the merge
  git merge --abort       put everything back as it was, any time

Edit `stock/aisle-b.md` so the line under B-14 reads exactly:

    38 rolls, confirmed by a second recount.

Delete the `<<<<<<<`, `=======` and `>>>>>>>` lines while you are in
there. They are text in your file, and leaving one behind is the most
common way this goes wrong.
