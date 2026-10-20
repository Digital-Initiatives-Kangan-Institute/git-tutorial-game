No new commands. This time nobody tells you which command goes with
which file.

Marta's rule: one job per booking. Three sheets have changed and they
want three different things:

  dispatch/log.md    finished       commit it
  stock/aisle-b.md   Theo's draft   keep it, but do not commit it
  README.md          a typo         throw it away

And someone has already put the wrong one on the packing bench.

Everything you need you have already used:

  git add <path>               stage it
  git restore --staged <path>  unstage it, keeping the text
  git restore <path>           throw the edit away
  git diff --staged            check before committing

  try:  git status
        git diff
        git diff --staged

Make exactly one new commit, containing only the dispatch log line,
with the aisle B draft still pending and the README typo gone.
