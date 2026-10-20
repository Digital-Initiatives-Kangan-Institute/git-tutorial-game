Back on `main`, and nothing was lost, because nothing was ever at risk.
You read an old version of the records and then stopped reading it.

Worth keeping, because the panic around this state is out of all
proportion to what it is:

  detached HEAD means HEAD points at a commit, not at a branch

The files on disk are that commit's files. `git switch <branch>` ends
it. The only thing to be careful about is committing while you are out
there, because a commit with no branch pointing at it is easy to walk
away from.

Which is the subject of the rest of this act. Git keeps a gate log of
everywhere HEAD has been, and that log is why "lost track of" and
"gone" are different words.
