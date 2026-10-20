Both commits are at Head Office, and nothing was overwritten to get
them there.

You asked to force. The lease compared what your repository believed
about `origin/stocktake-plan` with what Head Office actually had. They
differed, because Ines had pushed, so git refused. Plain `--force`
would not have asked, and her commit would have vanished from Head
Office.

The refusal is a prompt to look, not a wall. If their work should stay,
merge and push normally, as you did. If the branch really is only
yours, fetch, and the lease will let the force through. Next job: that
last case, and what it can still cost.
