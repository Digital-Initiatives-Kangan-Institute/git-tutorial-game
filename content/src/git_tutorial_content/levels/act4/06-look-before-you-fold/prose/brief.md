Fetch, read what is waiting, then merge it.

  git fetch
  git status                             how far behind
  git log --oneline main..origin/main    the commits in the gap
  git diff --stat main origin/main       the files they touch
  git merge --no-edit origin/main

Both answers are readable before you merge. The merge itself is quiet:
the two edits are at different ends of the file.
