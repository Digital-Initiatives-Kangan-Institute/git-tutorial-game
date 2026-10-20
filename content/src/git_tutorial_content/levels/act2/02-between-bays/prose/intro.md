You opened a bay last job. This one is about what happens when you
step out of it.

There is now a fit-out page committed on the `aisle-d-fitout` branch,
and `main` has never seen it. Your working tree can only show one
branch at a time, so when you switch, git rewrites the files on disk
to match the branch you asked for. Drive the forklift to another shelf
line and the loading floor is laid out the way that line has it.

  git switch <name>    move to a branch that already exists

The first time this happens it looks like a disaster. You switch to
`main` and the page is gone from the folder. It is not gone from the
repository: it is in a commit, and that commit is on the other branch.
Switch back and it returns.

That is the difference between a branch and a backup. A branch does
not keep a second copy of your files beside the first. It keeps a
second line of history, and the folder shows whichever line you are
standing on.

  try:  git branch
        ls docs
        git switch main
        ls docs

Finish on `main`, with the page still committed on `aisle-d-fitout`.
Do not copy the file anywhere, and do not commit it to `main`.
