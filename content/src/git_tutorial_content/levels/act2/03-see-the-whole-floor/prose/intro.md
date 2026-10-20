While you were out of the `aisle-d-fitout` bay, Theo booked a record
in on `main`. Both branches have moved since they parted. That is the
normal state of a busy warehouse's records, and it is the state people
find hardest to picture.

`git log` only shows the history behind one place. To see more than
one branch at once you have to ask for the whole floor plan:

  git log --graph --all --oneline

`--all` means every branch, not just the one you are on. `--graph`
draws the lines down the left so you can see where they split.

Read the drawing from the bottom up. The lines begin as one: the
commit where they join is the last thing both branches agree on. Above
it they separate, and each side's commits belong only to that side.

There is a second way to ask, in plain numbers:

  git log --oneline main..aisle-d-fitout    on the bay, not on main
  git log --oneline aisle-d-fitout..main    on main, not on the bay

The two dots mean "reachable from the right, but not from the left".

  try:  git log --graph --all --oneline
        git log --oneline main..aisle-d-fitout
        git log --oneline aisle-d-fitout..main

Answer the three questions on the job sheet. Change nothing.
