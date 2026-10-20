Incident report from Marta: three commits this morning. You counted bin
B-15, noted the count in the dispatch log, and added a step to the
receiving procedure about the scanner receipt.

Then you went to un-commit the last one, to fold it into the others,
and typed this:

    git reset --hard HEAD~3

`--soft` was what you meant. One word, and `git log` now ends at last
week's dispatches. The files are back to how they were before
breakfast. B-15 says "Not counted yet."

Nothing is gone, and you already know why: a branch label moved, and the
commits it used to point at are crates out in the yard. The gate log
route from the cleared-bay job works here too: find the hash, move
`main` back to it.

But there is something quicker, and it is worth meeting properly
because it is the thing git does *for* you:

    ORIG_HEAD

Before any operation that moves HEAD a long way (reset, merge, rebase,
pull) git writes the position you were at into *`ORIG_HEAD`*. It is the
undo marker: an ordinary name you can use anywhere a commit is wanted.
`git log ORIG_HEAD`, `git diff ORIG_HEAD`, and the one that matters
here:

    git reset --hard ORIG_HEAD

It holds exactly one position, the one before the *last* such move. It
is the undo for the thing you just did, not a history. The reflog is
the history.

  try:  git log --oneline
        git reflog
        git log --oneline -n 1 ORIG_HEAD

All three commits back on `main`, files and all, with no merge commit.
