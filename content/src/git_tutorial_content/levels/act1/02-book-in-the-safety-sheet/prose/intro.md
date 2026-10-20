Marta has written a safety sheet for the floor and left it in the
records folder. It is not booked in yet. That is your job.

Saving a change in git takes two steps, not one.

  1  git add     stage the change: mark it to go in the next commit
  2  git commit  record everything staged, as one commit

Think of the *staging area* as the packing bench: you carry things to
it from the loading floor (the *working tree*), and a commit seals
whatever is on the bench. The staging area is also called the index.
Both names mean the same thing. It exists so you can choose exactly
what goes into a commit instead of saving everything at once.

A file git is not tracking is called *untracked*. `git status` still
lists it, because git can see it perfectly well, but its contents are
not in the history until you say so. There is one here now:
`docs/safety.md`, already written.

  try:  git status
        cat docs/safety.md

Get that file into the history as one new commit, and run `git status`
before, between and after the two steps.
