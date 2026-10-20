Until now there has been one line of records, and everyone has booked
in at the end of it. That stops working the moment two jobs are on the
go at once.

Marta has a new job for you: the paperwork for the aisle D fit-out.
New racking, new bays, a page describing it. It is not finished work,
so it does not go on `main` with everything else. It gets a job bay of
its own.

In git that bay is a *branch*. A branch is a name that points at a
commit, and that is the whole of it. It is not a copy of the records,
not a folder, and making one does not change a single file.

  git branch              list the branches that exist
  git switch -c <name>    make a branch here and move onto it

The branch you have been on all along is called `main`. A new branch
starts at the commit you are standing on. From then on the two names
move independently: commits you make go onto the branch you are on,
and the other one stays put.

  try:  git status
        git branch
        git log --oneline

Make a branch called `aisle-d-fitout` and stand on it. Write nothing yet.
