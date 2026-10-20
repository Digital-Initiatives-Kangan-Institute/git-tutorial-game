Theo puts his head round the door. "My aisle C branch has gone from
Head Office. Did somebody bin my count?"

Your repository still lists `origin/aisle-c-count`, because the last
time you fetched, it was there. That name is only a note. Head Office
may have done anything with the branch since.

Find out before anyone panics. Two things in your repository are out
of date:

    origin/aisle-c-count   a note for a branch Head Office deleted
    main                   behind whatever Head Office did next

`git fetch --prune` deals with the first: it brings Head Office's news
and takes down notes for branches that are gone. `git pull` deals with
the second. Then `git log --graph` tells Theo what happened to his
work.

A deleted branch is a deleted *name*. If its commits were merged
first, they are as safe as anything else in `main`.

  try:  git branch -r
        git fetch --prune
        git log --oneline --graph --all -n 5

Then bring `main` up to date and tell Theo who merged his count.
