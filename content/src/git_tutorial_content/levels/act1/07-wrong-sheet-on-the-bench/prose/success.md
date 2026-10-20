The procedure reads as Ines wrote it, and nothing is pending.

The order was the whole point. `git restore` copies the staging area
onto the file on disk, not the last commit. In the other order it
would have swapped one unwanted version for the other and left
`git status` still reporting a staged change.

A command that sounds like "undo" is really "copy from here to
there". Once you know which way each one moves, you can work out what
it will do in a situation nobody has shown you. Next job, three
changes, and you decide what happens to each.
