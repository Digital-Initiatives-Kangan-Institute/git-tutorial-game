You are on `main`, the page is not in the folder, and it is still on
`aisle-d-fitout` exactly as you left it.

The file did leave the folder. You watched it go. What did not happen
is losing it: the commit still holds it, on the branch you made it on,
and `git switch` only ever rewrites the folder to match where you are
standing.

  git log --oneline aisle-d-fitout

You can read another branch's history from here without going there.
Later in this act you will bring that work into `main` on purpose,
which is the only way it ever arrives. Next: see both lines at once.
