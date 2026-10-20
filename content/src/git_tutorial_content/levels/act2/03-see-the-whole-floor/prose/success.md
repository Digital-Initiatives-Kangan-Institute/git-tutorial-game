Two commits on one side, one on the other, and a shared commit
underneath them both.

That shape has words people use constantly: your branch is two commits
*ahead* of main and one commit *behind* it. Ahead and behind are
always measured against something, counted from the commit where the
two last agreed.

  git log --graph --all --oneline

Keep running that. A surprising amount of git trouble is someone
acting on a shape they have not looked at, and it is three words to
ask.

Nothing has been merged yet. The rest of this act is about bringing
lines back together. First, though, a rush order.
