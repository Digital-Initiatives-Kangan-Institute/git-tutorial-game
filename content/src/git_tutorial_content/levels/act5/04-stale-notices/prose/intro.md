Last week four branches went up to Head Office: Theo's Fennick order,
Marta's pallet audit, and two of Ines's. You fetched, and your
repository has an `origin/*` name for each.

Since then Ines has been tidying. She deleted three of them at Head
Office, the way you deleted `peak-rota`. Your repository was not told.

Remember what `origin/main` is: not Head Office's branch, but your
*note* of where it was the last time you fetched. The same goes for
every `origin/*` name. Fetching updates the notes and adds new ones,
but it never takes one down, so notes for deleted branches stay on
the board for ever.

    git fetch --prune    fetch, and remove notes for branches that
                         Head Office no longer has

Pruning only ever touches `origin/*` names. Your own branches, and
any commits, are left alone.

  try:  git branch -r
        git fetch
        git branch -r
        git fetch --prune

Then answer the two questions on the job sheet.
