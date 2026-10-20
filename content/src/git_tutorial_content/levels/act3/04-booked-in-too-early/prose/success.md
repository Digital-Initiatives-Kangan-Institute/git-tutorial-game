One commit, and it says what you meant it to say.

Nothing about that was a repair. `--soft` moved the label back and left
everything else alone, so the work was never at risk: it went from "in
a commit" to "staged", and staged is somewhere you have stood since
Act 1.

The thing to watch is who else has seen the commit. You rewrote history
here: the first commit still exists, out in the yard, and what is on
`main` now is a *different* commit with a different hash. That costs
nothing while the commit is only on your machine, and causes trouble
once it has gone up to Head Office.

  before you have pushed    reset is yours, use it freely
  after you have pushed     leave the history alone

If you remember one form of this command, make it `git reset --soft
HEAD~1`: it un-commits and keeps everything. Next job, the same command
with the dial turned one notch.
