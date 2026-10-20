Bring `racking-checks` into `main`. Both branches have moved, so this
one makes a merge commit.

  git switch main
  git merge racking-checks --no-edit

`--no-edit` accepts the message git writes instead of opening an
editor. Without it an editor opens; save and close it to accept.

A merge commit is the only kind with more than one parent, one per
side. It is not an error and not something you did wrong. It is how
git records that two lines of work came back together.
