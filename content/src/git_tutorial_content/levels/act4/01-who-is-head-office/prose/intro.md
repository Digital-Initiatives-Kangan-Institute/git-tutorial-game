Every record you have booked in so far went into one folder on one
machine. Marta wants you to know where that folder came from, because
from here on other people are involved.

On your first shift the tutorial ran `git clone`. Everything since,
every commit and every branch, happened in a *clone*: a complete copy
of a repository that lives somewhere else. That somewhere else is
Head Office.

    git clone <address> <folder>

A clone is not a download of the latest version. It is the whole
repository: every commit, every branch, the full history, all of it
local. That is why everything so far worked with no network, and why
`git log` is instant.

A clone also remembers where it came from. That address is a *remote*,
and the one you cloned from is called `origin` by convention. For you,
`origin` is Head Office:

    git remote -v

To see what a new starter gets, make another copy. Put it next to this
folder, not inside it, so it does not get mixed in with your work:

    git clone "$(git remote get-url origin)" ../new-starter

  try:  git remote -v
        git log --oneline

Then answer the two questions on the job sheet.
