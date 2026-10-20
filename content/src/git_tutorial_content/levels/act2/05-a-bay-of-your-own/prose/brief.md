Create a branch `racking-checks`, write `docs/racking-checks.md`, and
commit it there. Finish standing on the branch with `main` unmoved.

  git switch -c <name>    make a branch here and move onto it
  git add <path>          stage it
  git commit -m "..."     record it

Any content in the page counts. Nobody is marking your writing, only
that the file is committed on `racking-checks` and not on `main`.

Branch first out of habit, though writing first is not a trap: an
uncommitted edit follows you across `git switch -c`. What decides
where the work lands is which branch you are on when you commit.
