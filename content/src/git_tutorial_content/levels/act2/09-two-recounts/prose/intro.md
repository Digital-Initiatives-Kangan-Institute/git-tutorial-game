Two people counted bin B-14. Theo, on `main`, wrote "38 rolls on the
shelf after the Fennick order." Your recount, on `recount-b14`, says
"36 rolls on the shelf. Two were torn and binned." Same file, same
line.

Git combines work by looking at what each side changed. When the two
sides changed different things it works them out alone, which is what
happened in the last merges. When they changed the *same* lines it has
no way to choose, so it stops and asks.

That pause is a *conflict*: the crate is held at inspection. It is not
an error and nothing is broken. Git has done as much of the merge as
it can and is waiting for a decision only a person can make.

While it waits, it writes both versions into the file, fenced off:

    <<<<<<< HEAD
    the version on the branch you are on
    =======
    the version on the branch you are merging
    >>>>>>> recount-b14

Those marker lines are ordinary text in your file. Resolving the
conflict means editing that file until it says what it should, and
deleting the markers is part of the job, not something git does after.
Then `git add` the file, which tells git this one is settled, and
commit to finish the merge.

Marta did a third count and settled it: 38 rolls.

**If you want out at any point:**

  git merge --abort

That puts the repository back exactly as it was before you started. It
is always there while a merge is paused, and knowing it is there is
what makes starting a merge safe.

  try:  git log --oneline --graph --all
        git merge recount-b14
        git status

Finish with one merge commit on `main`, no markers left, and the B-14
line reading exactly:

    38 rolls, confirmed by a second recount.
