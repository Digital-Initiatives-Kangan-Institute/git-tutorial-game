Three pending changes, three different outcomes:

  dispatch/log.md    finished: commit it
  stock/aisle-b.md   half-written: keep it, do not commit it
  README.md          a typo: throw it away

  git add <path>                stage it
  git restore --staged <path>   unstage it, keeping the text
  git restore <path>            throw the edit away
  git diff --staged             check before committing

Exactly one new commit when you are done, with the aisle B draft
still pending. Note which file is staged when you start. It is not
the one you want.
