Welcome to Tallowmere Distribution. Before you move a single pallet,
Marta wants you to walk the floor and read the records.

The records live in a git *repository*: a folder plus a complete
history of every change anyone has made to it. Each saved change is a
*commit*, with a message, an author, and a unique id called a hash.

Two commands read that history. Neither changes anything, so you can
run them as often as you like:

  git status   which branch you are on, and what has changed
  git log      every commit, newest first

`git status` will also mention `origin/main`. `origin` is Head Office's
copy of these records. Nothing in this first shift sends anything
there, so read those lines as news from head office, not as a task.

  try:  git status
        git log --oneline
        git log

Then answer the four questions on the job sheet.
