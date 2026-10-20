That is the whole trick, and the rest of this act is built on it.

The reflog is a record git writes for itself every time HEAD moves. No
setting to turn on, nothing to remember in advance: it has been
recording since your first commit, including every move you made in
Act 2.

Two things follow from that:

  Work you cannot see is not work that is gone. A commit with nothing
  pointing at it is invisible to `git log` and intact on disk.

  Every risky thing you do leaves a line saying where you were before
  you did it. Which means it can be undone.

It is a local record of your own repository. It is not sent up to Head
Office, and a colleague's reflog is not yours. Entries are kept for
ninety days by default, long past the point where you would notice.

Next job: the commits are still there. Go and get them.
