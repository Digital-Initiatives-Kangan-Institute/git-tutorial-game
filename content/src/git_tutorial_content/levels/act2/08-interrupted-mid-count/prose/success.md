Both edits are committed on `aisle-b-count` and the stash is empty.

If you ran `git status` after the pop and your staged file was no
longer staged, nothing went wrong: that is what `pop` does unless you
give it `--index`. The text is the part it guarantees, and `git add`
puts the staging back in a second.

  git stash list

The pattern is the same every time: pending work goes aside, you deal
with something else, the work comes back. The only thing to watch is
leaving things in there. It is a stack with no names, and by Thursday
nobody knows what `stash@{2}` was. Work you want to keep overnight
belongs on a branch.

Next: two people count the same bin.
