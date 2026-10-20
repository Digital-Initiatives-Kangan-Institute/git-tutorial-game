Theo recounted the B-14 pallet wrap first thing: 36 rolls, not 40. He
typed the new figure into `stock/aisle-b.md` on the shared terminal and
went out to meet a delivery. It is on your screen, not yet committed.

Marta wants it booked, sent up, and sealed, because the Easter order to
Kestrelby is based on it.

Order matters here. A *tag* goes on a commit, so the commit has to
exist first:

    git diff                       read Theo's change
    git commit                     book it on main
    git push                       send main up
    git tag recount-b14            seal HEAD, the commit you just made
    git push origin recount-b14    send the seal up

Last time you tagged an older commit by its hash. This time the commit
you want is `HEAD`, so the hash can be left off.

And `git push` on its own never sends tags. Each one goes up by name.

  try:  git status
        git diff

Book it, send it, seal it, send the seal.
