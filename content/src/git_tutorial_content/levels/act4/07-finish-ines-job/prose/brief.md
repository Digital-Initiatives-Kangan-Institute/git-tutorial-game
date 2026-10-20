Ines's branch is at Head Office. Finish her sentence and send it back.

  git fetch                       so your repository knows the branch
  git branch -r                   what the remote has
  git switch returns-procedure    local branch from hers, paired with it
  git add docs/receiving.md
  git commit -m "Finish the returns sentence"
  git push                        no arguments needed

The sentence in `docs/receiving.md` should read:

    Returned pallets are booked in against the original delivery note.

Build on her commit. A fresh branch with the same text would throw
hers away.
