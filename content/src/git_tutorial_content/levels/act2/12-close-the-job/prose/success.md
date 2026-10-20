Both files settled, one merge commit, and the aisle D job closed.

That is Act 2. Look at what you can now do that you could not a few
hours ago:

  git log --oneline --graph --all

You can read that picture. You can open a branch, work on it, and know
why your files change when you switch. You can put unfinished work
aside and get it back. You can merge, and tell in advance whether it
will fast-forward or make a merge commit. And when two people have
written over each other you can settle it, or back out and settle it
tomorrow.

Conflicts are routine. They are not a sign anyone did anything wrong,
and the whole skill is reading which files are unresolved and working
through them one at a time. The only real trap is leaving a merge
half-finished, and you know the way out of that one.

Act 3 is about the other thing that happens: work that looks lost.
