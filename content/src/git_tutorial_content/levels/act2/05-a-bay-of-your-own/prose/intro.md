No new commands. This is the branch cycle end to end, with nobody
naming the steps for you.

Marta wants a weekly racking checklist: what to look for on the
Monday walk round, and what to do about it. The work gets a bay of its
own, as all work does now.

Everything you need you have used already:

  git switch -c <name>    make a branch here and move onto it
  git add <path>          stage what you wrote
  git commit -m "..."     record it
  git status              check between the steps

Branch first, out of habit. Not because writing first breaks anything:
an uncommitted edit belongs to no branch, so it follows you when you
switch, and `git switch -c` after writing lands the commit on the new
branch just the same. The habit matters because the commit is the part
that sticks to a branch, and deciding where it goes *before* you are
tired and typing `git commit` is how you stop yourself putting it on
`main` by reflex.

  try:  git status
        git branch
        git log --oneline --graph --all

Make a branch called `racking-checks`, commit `docs/racking-checks.md`
on it, and leave `main` exactly where it is. Any content is fine.
