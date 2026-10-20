Incident report from Theo: the aisle B figures look wrong, and he
asked you to check what the count said when it was first booked in.
An answer online said to run this, with the hash of the "Count aisle
B" commit:

    git checkout <hash>

So you did. The files changed under you, the prompt looks different,
and `git status` is saying something it has never said before.

Nothing is broken. You are *detached*.

Every other time you have moved around, HEAD pointed at a branch, and
the branch pointed at a commit. Commit, and the branch moves along with
you. A *detached HEAD* points straight at a commit with no branch in
between. In the warehouse picture, the forklift is parked at an old
crate in the middle of a shelf line, not at the end of one.

Reading from here is fine, and reading is what the state is for. The
risk is committing: there is no branch to move, so a new commit would
have nothing pointing at it, and walking away would leave it with no
name anywhere. That is the whole danger, and it is real but small.

About `checkout`: it is the old command that did two unrelated jobs,
moving between branches and restoring files. That is why you learned
`switch` and `restore` instead. You will meet `checkout` in every answer
you ever search for, so it is worth recognising. You do not need to use
it.

  try:  git status
        git log --oneline

Note which commit you were standing on, then get back to `main`.
