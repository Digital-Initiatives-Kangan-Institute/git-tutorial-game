You are halfway through the stocktake plan on the `stocktake-prep`
branch. The last edit is not committed, and it is not finished enough
to be. Then Theo rings: a rush order for Fennick Garden Centre has
gone out, and it needs logging on `main`, now.

Try switching. Git refuses, and the message is worth reading: the page
you have edited does not exist on `main`, so moving there would mean
deleting your change. Git will not do that silently.

That is not a rule that you can never switch with work pending. Often
you can, and the edit simply comes with you. It is refused when
carrying it across would mean losing it.

Committing half a sentence to get unstuck is the wrong answer: the
history is not a save button. There is a back room for pending work:

  git stash       take every pending change off to one side
  git stash pop   put the most recent set back

`git stash` leaves your tracked files exactly as the last commit has
them, which is what makes the switch allowed. The changes are not lost
and not committed; they wait to one side until you ask for them.

One exception: untracked files stay where they are. `git stash` only
takes files git already tracks. For the rest there is `git stash -u`.

`pop` is the opposite, and the word is literal: it takes the top set
off the pile and puts it back in your folder.

  try:  git status
        git switch main
        git stash
        git status

Log the rush order on `main`, then come back to `stocktake-prep` with
your unfinished page in front of you and nothing left in the stash.
