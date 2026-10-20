Thursday, one o'clock. You pulled, and the pull stopped: Theo's count
of bin B-15 says 24 bundles and yours says 22. You had just opened
`stock/aisle-b.md` when Marta rang.

Fennick Garden Centre want two pallets of cartons by three, and the
dispatch note has to be booked now. You had started it before lunch:
`dispatch/2026-03-26.md` is on disk, half written, not committed.

Here is the trap. While a merge is stopped, `git commit` does not make
an ordinary commit. It *finishes the merge*. Add the rush note and
commit, and it goes into the merge commit, tangled up with a stock
count you have not settled.

So: not now. Back out of the merge completely:

    git merge --abort

That puts the repository back exactly as it was before you pulled:
your commit, no markers, nothing held. Files that were never part of
the merge, like the untracked rush note, are left alone. Then the rush
job, on its own, and then the pull again. It will stop in exactly the
same place, because nothing about the disagreement has changed. You
just have time for it now.

Marta's call on B-15, when you get there: your 22 stands.

  try:  git status
        git merge --abort
        git status

Rush note first, then the count.
