You wrote up after-hours deliveries before lunch and committed it.
Ines corrected the pallet wrap price at Head Office while you were out.

So you come back, type `git push`, and get this:

    ! [rejected]        main -> main (fetch first)
    error: failed to push some refs to '...'
    hint: Updates were rejected because the remote contains work that
    hint: you do not have locally.

Head Office has refused your records, because it has newer ones. Nothing
is broken and nothing is lost: git has just stopped you deleting Ines's
correction.

Push moves the branch at Head Office to point at your commit. Yours
does not have hers in its history, so moving the branch there would
leave her commit with nothing pointing at it. Git will not do that by
default. A branch on a remote may only move *forwards*, to a commit
that already contains what is there.

That tells you the fix. Take her commit, combine it with yours, and
then yours does contain hers:

    git pull        fetch and merge, as in the last job
    git push        now accepted

  try:  git push
        git status

Ines's correction and your write-up should both end up at Head Office.
