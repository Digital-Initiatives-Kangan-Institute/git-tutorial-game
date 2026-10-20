Two commits on `returns-procedure`: hers, and yours on top. Both at
Head Office, and she can pick it up tomorrow by pulling.

`git switch <name>` with no `-c`, for a branch only the remote has,
does three things: makes a local branch at the remote branch's commit,
sets its upstream, and switches to it. If git says there is no such
branch, you have not fetched since it was pushed.

When you commit on someone else's branch, push promptly. Work sitting
on your machine is work they cannot see and might redo. Next job: an
ordinary morning.
