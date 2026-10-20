Incident report from Marta: last week the Kestrelby bulk discount came
out of the price list. Nobody could find it in writing, so you reverted
the commit that added it, and the log has said so ever since:

    Revert "Add the Kestrelby bulk discount"

The discount is real. Ines found the signed letter this morning. It
needs to go back.

You could open `suppliers/price-list.md` and type it in again. Nobody
would notice, and it would be the wrong instinct: the text is in this
repository twice already, and retyping it is how two slightly different
versions of the same paragraph get into the records.

Here is the thing worth seeing: *the revert is an ordinary commit.* Not
a special kind of entry, not a mark against the commit it undid, not a
gap in the history. A correction crate is still a crate. It changed
some lines, like every other commit, and it has a hash of its own.

So undo it the same way you undid anything else.

    git revert <the hash of the revert>

Reverting a revert restores the original change and leaves all three
commits standing: what was added, what was taken out, and what was put
back. Anyone reading the log can see the decision being made and
unmade, which is what happened.

  try:  git log --oneline
        git show HEAD

The discount back on the price list, as a new commit, with nothing removed.
