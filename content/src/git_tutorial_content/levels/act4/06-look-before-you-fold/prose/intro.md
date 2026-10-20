You were in a meeting. Two commits landed at Head Office.

`git pull` would take both and merge them, and most mornings that is
the right move. This job is about the mornings when it is worth
looking first: when you have a commit of your own in the same file,
and finding that out *after* the merge is how an ordinary morning
turns into a conflict you did not expect.

So read the bulletin and stop. That is what `fetch` is for, and what
`pull` hides by doing both halves at once.

    git fetch
    git status                            how far behind
    git log --oneline main..origin/main   what is in the gap
    git diff --stat main origin/main      which files they touch

`main..origin/main` is the two-dot range you met earlier: commits on
the right that are not on the left. "What does Head Office have that I
do not."

Today it is quiet. You and Theo both wrote on the aisle B sheet, at
different ends, and git will combine those without asking anyone.

  try:  git fetch
        git status

Answer both questions, then merge their work into your `main`.
