Ines here. Small thing, but it matters.

Yesterday you deleted `docs/receiving.md` and committed, on the grounds
that the scanner's BOOK-IN screens walk drivers through it now. They do
not cover chilled loads, and that is exactly what I had just added to
the sheet at Head Office. The sheet stays.

Three jobs ago you met *modify/delete*: you changed a file, Head Office
deleted it. This is the same conflict the other way round: you deleted,
Head Office changed. `git status` lists the file as "deleted by us",
and git leaves Head Office's version on disk while it waits.

Last time the answer was `git rm`, to agree with the deletion. This
time it is the opposite: keep Head Office's count of it, whole.

    git restore --theirs docs/receiving.md

makes the file exactly my version, and `git add` keeps it. That is all
settling a deleted file takes: `git rm` says "gone", `git add` says
"here".

  try:  git pull
        git status
        git restore --theirs docs/receiving.md

Ines
