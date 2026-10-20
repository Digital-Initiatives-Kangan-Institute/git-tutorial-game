Clean working tree, no paused merge, and `main` exactly as it was. The
`recount-b14` branch still has its commit.

That is the whole point of `--abort`: a complete undo, not a partial
one. The files, the staging area and the branch all go back. Git does
keep a private note of where you were, which is what Act 3 is built
on, but nothing about the attempt is in your history.

Three things you can do from a conflict, and two of them are fine:

  finish it     resolve, add, commit
  back out      git merge --abort
  leave it      the worst option, and the easiest to do by accident

A repository paused mid-merge looks almost normal, and the markers are
just text sitting in your files. People commit them. If you are not
going to finish a merge now, abort it now.

Next: two jobs at once.
