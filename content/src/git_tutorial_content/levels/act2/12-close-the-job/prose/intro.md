The aisle D fit-out is finished, and Marta wants it closed out. The
`aisle-d-signoff` branch logs the sign-off and tells drivers that
out-of-hours deliveries can now go to aisle D. Meanwhile Theo, on
`main`, logged the Fennick dispatch and told drivers to wait by gate 2.
Both sides edited `dispatch/log.md` and both edited `README.md`, so
this merge stops twice.

Nothing new to learn. What changes is that resolving one file does not
finish the merge, and that is the part people get wrong: they fix the
first conflict, type `git commit`, and git refuses because the other
file is still unresolved.

Use `git status` as a scoreboard. It lists every file still held at
inspection, and a file leaves that list when you `git add` it. Staging
is how you say "this one is settled". It is not optional bookkeeping;
it is the signal git is waiting for. When the list is empty, commit.

The two files want different answers:

  dispatch/log.md   both entries are true, so keep both, one per line
  README.md         the two lines are both partly right, so write one
                    that covers both, using the exact phrase
                    `gate 2 or in aisle D` so the check can find it

That second kind is the common one, and it is why conflicts cannot be
automated. Picking "theirs" or "mine" wholesale would lose something.
You are not choosing a side; you are writing the version that should
have been there.

  try:  git log --oneline --graph --all
        git merge aisle-d-signoff
        git status

Finish with one merge commit, both log lines present, the README
saying `gate 2 or in aisle D`, and no markers left anywhere.
