Two jobs, two branches, neither on top of the other, and your
unfinished page exactly as you left it.

The move you made here is the one that keeps a week tidy: when a job
arrives, go to `main` first and branch from there. Branches made from
whatever you happened to be standing on are how people end up asking
why a colleague's half-finished work is in their merge.

  git log --oneline --graph --all

Each branch starts from `main` and knows nothing about the other,
which is exactly right: each can be merged, or abandoned, on its own.
And the stash held your work across all of it without a commit you
would have been embarrassed by.

One job left in this act: closing one out.
