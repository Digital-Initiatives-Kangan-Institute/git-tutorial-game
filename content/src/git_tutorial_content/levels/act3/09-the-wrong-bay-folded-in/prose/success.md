The cartons fix is on `main`, `month-end` is exactly where Theo left
it, and there is no trace of the merge that should not have started.

Three ways out of a merge, and which one depends only on *when* you
noticed:

  while it is paused       git merge --abort
                           nothing happened; there is nothing to undo

  after it is committed    the merge is a commit, so this act's undos
                           apply: reset it if it is yours, revert it
                           if it is shared

  paused, and you want     resolve, add, commit: Act 2's work
  it finished

The habit that saves the most time: when a merge stops, read
`git status` before you start resolving. It names the branch coming in.
Next job, the last of the act: three mistakes, three different undos.
