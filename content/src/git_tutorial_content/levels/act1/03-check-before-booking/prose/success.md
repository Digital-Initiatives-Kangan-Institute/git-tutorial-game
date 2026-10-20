One commit, containing one change, and Theo's aisle B count still in
your working tree untouched.

That is what the staging area is for. It is not an extra step between
you and a commit; it is where you decide what the commit is going to
be. `git diff --staged` asks "what am I about to record?", and asking
it every time is the habit that stops you booking in the wrong thing.

Three places now matter:

  the last commit         what is recorded
  the staging area        what will be recorded next
  the working tree        the files as they are right now

Next job, you finish something someone else started.
