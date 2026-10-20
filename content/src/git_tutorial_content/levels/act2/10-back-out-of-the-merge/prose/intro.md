This job starts in the middle. Somebody began merging the B-14
recount, hit the conflict, and went home. The repository is still
sitting in it, held at inspection, and it is yours now.

(Each job sets its own scene, so this is not the merge you finished a
moment ago. It is the same two branches set up again, left paused this
time.)

That state is sticky on purpose. Until you either finish it or cancel
it, `git status` opens by telling you a merge is in progress. Most
things still work: you can look, edit, stage and commit. But anything
that would take you somewhere else, another `git switch` or
`git merge`, is refused until this one is settled.

  git merge --abort

That is the cancel. It puts the working tree, the staging area and the
branch back exactly as they were before the merge started. Not
"mostly": the whole attempt is undone, and the branch you were merging
is untouched and still there to merge later.

You met it last job as a safety net. Here it is the answer. Backing
out is a legitimate thing to do with a merge: the work has not gone
anywhere, and the conflict will be the same conflict tomorrow, when
somebody has done the third count.

What is *not* safe is leaving it paused. A half-finished merge with
markers in the files is the state most likely to end up committed by
accident.

  try:  git status
        cat stock/aisle-b.md
        git log --oneline --graph --all

Back out: no merge in progress, no markers anywhere, `main` saying
exactly what it said before, and `recount-b14` still there.
