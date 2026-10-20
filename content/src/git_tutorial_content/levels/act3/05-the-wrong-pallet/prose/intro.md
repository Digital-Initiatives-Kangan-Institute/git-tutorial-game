Incident report from Theo: nothing in the README points at the dispatch
log, so you added a line to its procedures list and committed it with
the habit everybody has:

    git add .
    git commit -m "Link the dispatch log"

`scratch.md` was in the folder. Your notes. One line in it says *do not
let this file anywhere near the records*, and it is now in the history
of the records. The wrong pallet went into the crate with the right
one.

This is the most common way something gets committed that should not
be, and `add .` is why: it means "everything here", and everything here
includes whatever you left lying around.

The fix is the same command as last job with the dial turned one notch:

    --soft     move the label, leave everything staged
    --mixed    move the label, and unstage

`--mixed` is what `reset` does when you do not say. It un-commits and
then empties the staging area, so nothing is queued and you decide what
goes back in. A file that only existed in the commit you undid goes
back to being untracked: git stops knowing about it, and it stays on
your disk.

Which is exactly where you wanted those notes in the first place.

  try:  git show --stat HEAD
        git status

One commit holding the README link; `scratch.md` untracked and still on disk.
