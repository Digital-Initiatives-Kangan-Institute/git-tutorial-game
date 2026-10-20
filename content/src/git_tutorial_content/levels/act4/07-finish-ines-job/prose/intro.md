Ines started a returns procedure yesterday, pushed it to a branch
called `returns-procedure`, and is off sick today. The sentence stops
in the middle:

    Returned pallets are booked in against

It needs four more words. You are going to add them to her branch,
which means working on a branch that exists at Head Office and not
here.

`git branch` does not list it; that lists yours. After a fetch,
`git branch -r` lists what the remote has, and hers is there as
`origin/returns-procedure`.

Then:

    git switch returns-procedure

No `-c`. You are not creating a branch from nothing. When you name a
branch you do not have and the remote has one by that name, git makes
you a local branch from it and pairs the two, so a bare `git push`
sends your commits back to the same place.

That only works if you have fetched. A repository that has never seen
the branch cannot make you one from it.

  try:  git branch -r
        git fetch

The finished sentence should read: `Returned pallets are booked in
against the original delivery note.`
