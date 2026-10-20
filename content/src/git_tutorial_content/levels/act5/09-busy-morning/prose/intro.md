Easter week. You came in at seven and wrote up the peak season rules
for the loading bays before anyone else was about, and committed them
on `main`.

Two things happened that you have not seen yet. Theo sent the Easter
dispatches up to Head Office at five to seven. And yesterday afternoon
Ines withdrew her April slots draft and deleted the branch, though your
repository still lists `origin/april-slots`.

Neither is new. This is what an ordinary busy morning looks like:

    git push              refused: Head Office has Theo's commit
    git pull              fetch it and merge it with yours
    git push              accepted
    git fetch --prune     and take down the stale name

Pulling fetches, but a plain fetch never removes anything. That is why
the stale name is still there after the push succeeds.

  try:  git status
        git push
        git branch -r

Get your commit up without losing Theo's, and leave nothing listed
that Head Office does not have.
