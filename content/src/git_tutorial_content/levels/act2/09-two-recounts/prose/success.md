One count, no markers, and a merge commit holding both sides.

Be clear about what a conflict was and was not. Nothing was broken,
nothing was lost, and git was not confused. Two people changed the
same line, which is a question about what the stock record should say,
and no tool can answer that. Git did every part it could and stopped
at the part that was yours.

The shape of the fix is the same every time:

  1  start the merge and read which file stopped it
  2  edit that file until it reads correctly, markers deleted
  3  git add it, to say this one is settled
  4  commit, to finish the merge

And `git merge --abort` was there the whole way through. That matters
not because this merge was hard, but because the next one might be
ten files at eleven at night. Next job: use it.
