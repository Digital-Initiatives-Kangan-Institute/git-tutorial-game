Answer the three questions. Change nothing else: this job only reads.

  ahead    commits on aisle-d-fitout that main does not have
  behind   commits on main that aisle-d-fitout does not have
  base     the newest commit both branches share, as a short hash

A short hash is the seven-character form `git log --oneline` prints.

  git log --graph --all --oneline          every branch, lines drawn
  git log --oneline main..aisle-d-fitout   on the bay, not on main
  git log --oneline aisle-d-fitout..main   on main, not on the bay
  git merge-base main aisle-d-fitout       the commit they still share

Read the graph from the bottom. The lines start as one and separate at
the last commit both branches agree on.
