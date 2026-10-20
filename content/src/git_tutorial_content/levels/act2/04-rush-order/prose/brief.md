Add this line to `dispatch/log.md`, under "This week", and commit it
on `main`:

    - Rush order for Fennick Garden Centre dispatched.

Then come back to `stocktake-prep` with your unfinished page still
pending, and the stash empty.

  git stash       pending changes to one side, working tree clean
  git stash pop   the most recent set back again

Git refuses the switch because the edited page does not exist on
`main`. Do not commit the unfinished page to get round it, and do not
take it to `main`.
