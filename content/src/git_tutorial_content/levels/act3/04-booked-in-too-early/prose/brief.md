One commit, one line short. Undo the commit, keep the work, redo it
properly.

  git reset --soft HEAD~1   move main back one; files and staging untouched
  git status                see the changes still staged
  git diff --staged         exactly what the commit held
  git add dispatch/log.md
  git commit -m "Log the Fennick dispatch"

`HEAD~1` means "one commit before where I am". Both lines belong under
`## This week`:

    - Fennick Garden Centre order dispatched.
    - Third pallet marked fragile.

End with one commit on top of where `main` started, not two.
