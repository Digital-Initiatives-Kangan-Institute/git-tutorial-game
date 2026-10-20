Ines liked the rota. She merged `peak-rota` into `main` at Head Office
this morning, and her message says: "In. You can take the branch down."

A branch is only a name for a line of work. Once that work is merged,
the name has nothing left to do, and branches that are never cleared
up pile up until nobody can tell which ones are live. So: take the
shelf line down, here and at Head Office.

There are two copies of `peak-rota`, and each is deleted separately:

    git branch -d peak-rota            delete your branch
    git push origin --delete peak-rota ask Head Office to delete its one

`branch -d` is the careful delete. It refuses if the branch holds
commits that are not safely in another branch, so you cannot throw
work away by accident. (`-D` deletes without asking. Leave it alone.)

Do not take the merge on trust, though. Until you pull, your `main`
has no idea the rota was merged: Ines's merge commit is at Head Office
and nowhere else. Bring it in and look before you delete anything.

Deleting a branch never deletes its commits. They are in `main` now.

  try:  git status
        git switch main
        git pull
        git log --oneline --graph --all

Then take the branch down in both places.
