Ines at Head Office wants the B-15 cartons counted before she orders
more. The aisle B sheet still says "Not counted yet." You have been
down the aisle: twelve bundles.

The work is the kind you already know: a branch, an edit, a commit.
And when it is done, nobody else will be able to see it. Every record
you have booked in so far is in one folder on one machine.

    git push

Push sends commits from your repository up to a remote, and moves the
branch there to match yours. It is the opposite direction to `fetch`,
and just as narrow: it sends the branch you name, and nothing happens
to anyone else's files.

The first time you push a new branch, say where it belongs:

    git push -u origin count-b15

`-u` records `origin/count-b15` as the branch's *upstream*: the remote
branch it pairs with. After that, plain `git push` knows what you
mean, and `git status` can say whether Head Office is behind you.

  try:  git status
        git branch -vv

The line under B-15 should read exactly: `12 bundles in stock.`
