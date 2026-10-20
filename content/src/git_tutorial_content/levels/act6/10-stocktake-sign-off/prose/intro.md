Friday. The last count is in, and Marta wants the stocktake signed off
before anyone goes home.

Everything arrives in one pull. Since you last pulled, Theo sent up
his aisle B count, Ines sent up the April price list, and Ines retired
the stocktake checklist now that the counting is done. You, meanwhile,
committed your aisle B scan, the prices Kestrelby quoted, and ticks on
that same checklist.

So the pull will stop with three crates held, and each needs a
different answer:

    stock/aisle-b.md              both changed: Theo's B-14 count is
                                  right, your B-15 count is right.
                                  Edit it by hand to keep both.
    suppliers/price-list.md       both changed: Head Office's prices
                                  win whole. git restore --theirs.
    docs/stocktake-checklist.md   deleted by them: retired. git rm.

Read before you fix. `git status` gives each file's kind, and
`git log --merge` shows whose commits are on the other side. The
browser shows the same, with the count of blocks left in each file.

When nothing is held: commit, push, and only then seal it. A tag on a
commit Head Office does not have is a seal on the wrong crate:

    git tag stocktake-final
    git push origin stocktake-final

  try:  git pull
        git status
        git log --merge --oneline

Settle all three, push, and seal the stocktake.
