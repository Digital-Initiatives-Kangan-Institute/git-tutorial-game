Put both pending edits aside, come back to `aisle-b-count`, restore
them, and commit them there. Leave the stash empty and `main`
untouched. (Looking at `main` while the work is put aside is the point
of the exercise, but only the end state is checked.)

  git stash       every pending change aside, staged and not
  git stash pop   all of it back
  git stash list  what is being held

One edit is staged and one is not. Stash takes both. Expect to stage
again afterwards: `pop` restores your text but returns everything
unstaged, unless you ask for `--index`.
