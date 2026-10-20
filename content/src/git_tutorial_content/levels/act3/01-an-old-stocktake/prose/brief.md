You are standing on a commit rather than on a branch.

  git status            says where you are, in its first line
  git log --oneline     the commit you are on is the top one
  git switch main       go back
  git switch -          go back to wherever you were before

Type the hash of the commit you were standing on into the job sheet,
beside `detached_at`. Seven characters is enough.

Nothing here needs fixing. Reading from a detached HEAD is a normal
thing to do; the job is done once you have read where you were and
come back.
