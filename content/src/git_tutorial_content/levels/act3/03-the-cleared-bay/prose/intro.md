Incident report from Theo: yesterday you finished the 3 March dispatch
note for Fennick Garden Centre on a branch called `fennick-note`. You
finished the sentence that trailed off, and listed the three pallets
under it. This morning you were tidying up and ran:

    git branch -D fennick-note

Git did warn you. `-D` is the capital-letter version of `-d`: `-d`
refuses to delete a branch whose commits are not merged anywhere, and
`-D` does it anyway. You were tidying, not reading.

`git branch` does not list it. `git log` cannot reach it. Two commits of
work, and every tool you have used so far says they do not exist.

They do. Deleting a branch deletes *the name*, and nothing else. A
branch is a label pointing at a commit, and the commits it pointed at
are still in the repository exactly as you wrote them. The job bay was
cleared and its sign taken down; the crates were moved out to the yard,
not burnt.

The reflog does not walk backwards from a branch. It is the gate log of
where HEAD has been, and HEAD was standing on that work yesterday.

So: find the hash, then make a name point at it. You are not rebuilding
the work. You are putting the label back.

  try:  git branch
        git log --oneline
        git reflog

This job checks *how*: retyping the note would not be recovering it.
