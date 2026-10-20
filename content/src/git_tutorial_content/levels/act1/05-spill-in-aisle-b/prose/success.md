A clean working tree, and `git log` shows the history has not moved.

You just threw away work on purpose and the records did not notice,
because none of it was committed. Anything git has never recorded, it
cannot give back, which is what commits are for.

The three copies are the thing to carry out of this job. Once you can
say where a change is (commit, staging area or working tree), every
undo command in git becomes something you can reason about rather than
memorise. And `git status` was printing the right command, with your
filename in it, the whole time.

Next job, the scanner starts leaving files where git can see them.
