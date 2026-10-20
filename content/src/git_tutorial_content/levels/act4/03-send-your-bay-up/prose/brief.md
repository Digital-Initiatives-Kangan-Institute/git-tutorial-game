Do the work on a branch, then send it up.

  git switch -c count-b15
  git add stock/aisle-b.md
  git commit -m "Count the B-15 cartons"
  git push -u origin count-b15
  git branch -vv            which branch pairs with which

Under **B-15 Cartons, double wall** in `stock/aisle-b.md`, the line
should read exactly:

    12 bundles in stock.

Leave `main` alone; the branch is what Ines asked for.
