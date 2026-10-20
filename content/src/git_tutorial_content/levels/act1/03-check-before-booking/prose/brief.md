Two files have changed. One is staged, one is not. Commit the staged
one and leave the other pending.

  git status         which files have changed
  git diff           what changed, but is NOT staged
  git diff --staged  what changed and IS staged

In a diff, `+` is a line added and `-` is a line removed; a leading
space means the line is unchanged and only there for context.

`git commit` records what is staged and nothing else. You do not need
`git add` here: the right change is already staged, and adding the
other file would sweep it in too.
