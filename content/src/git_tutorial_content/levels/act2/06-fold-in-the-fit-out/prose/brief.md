Bring `aisle-d-fitout` into `main`. Finish standing on `main`, with
both names pointing at the same commit.

  git switch main      merging goes into the branch you are on
  git merge <name>     name the branch you want to bring in

Direction matters: stand on the branch that receives the work, name
the branch the work is on.

`main` has no commits of its own since the branch started, so git will
move the name forward instead of making a merge commit. That is a
fast-forward, and the history stays one straight line.
