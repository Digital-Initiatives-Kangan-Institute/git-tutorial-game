Stocktake week. Everyone is counting at once, and everyone is sending
counts up to Head Office as they go.

You counted bin B-14 first thing and committed it: 39 rolls. You have
not pushed yet. Theo counted the same bin twenty minutes earlier, got
37, and sent his straight up.

In Act 4 every pull went through on its own, because you and your
colleagues had changed different lines. This time two people changed
the *same* line of `stock/aisle-b.md`, so when you pull, git fetches
Theo's commit, starts the merge, and stops:

    CONFLICT (content): Merge conflict in stock/aisle-b.md
    Automatic merge failed; fix conflicts and then commit the result.

It is the conflict from Act 2, arriving through `git pull` instead of
`git merge`. The crate is held at inspection until somebody decides.
The file holds both figures between `<<<<<<<` and `>>>>>>>` lines, and
the browser shows the file as "both changed", with a count of blocks
still to settle.

Marta walked the aisle herself and settled it: 38 rolls. Write that,
delete the markers, `git add` the file, commit, and push.

  try:  git status
        git pull
        git status

Settle B-14 at 38 and send it up.
