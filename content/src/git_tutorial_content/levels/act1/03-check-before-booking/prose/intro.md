Theo has left two changes lying about. One is already on the packing
bench, ready to book in. The other is his count of a new bin in aisle
B, which he has not finished and is still on the loading floor.

`git status` lists which files have changed. It does not show what
changed inside them. Two commands do that, and they show different
things:

  git diff           changes that are NOT staged
  git diff --staged  changes that ARE staged

Each change is in one list or the other, and which one decides whether
the next commit includes it.

A *diff* is not a copy of the file. It shows only the parts that
changed, with a few unchanged lines around them so you can see where
you are:

  @@ -7,3 +7,7 @@ **B-15 Cartons, double wall**
   Not counted yet.
  +
  +**B-16 Strapping, 12mm**

Read the first character of each line and the rest follows:

  +       this line was added
  -       this line was removed
  space   unchanged, shown only so you can see the surroundings

There is no "changed" marker. A line you edited appears twice, once
as `-` and once as `+`. `@@ -7,3 +7,7 @@` locates the chunk: from line
7, three lines became seven. Above the first `@@`, git is talking to
itself (`diff --git`, `index`, `--- a/` and `+++ b/`). You can skip it.

  try:  git status
        git diff
        git diff --staged

Commit the *staged* change only, and leave the other one alone.
Because `git commit` records only what is staged, this needs no
`git add` at all.
