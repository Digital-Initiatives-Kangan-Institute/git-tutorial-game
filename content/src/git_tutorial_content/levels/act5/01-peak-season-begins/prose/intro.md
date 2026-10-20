Easter is a fortnight away and Tallowmere is going into peak season:
longer hours, more deliveries, and more people booking records into
the same repository at the same time.

That last part is what this act is about. You already know every
command for working with Head Office. Peak season is where you use
them with other people, every day, without thinking.

Marta wants a rota for the peak weeks, written on a branch of its own
and sent up so Ines can look at it. Before you start, though: Theo was
in early and sent something up to Head Office. Your `main` does not
have it yet.

The order is the habit:

    git pull                     take Head Office's updates first
    git switch -c peak-rota      then branch from the fresh main
    git push -u origin peak-rota and send the branch up when done

A *branch* starts from the commit you are on when you create it. Pull
after branching and your rota is built on last week's records.

  try:  git status
        git pull
        git log --oneline -n 3

Then write the rota and send it up.
