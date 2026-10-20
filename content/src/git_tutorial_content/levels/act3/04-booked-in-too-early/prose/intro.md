Incident report from Marta: you logged the Fennick Garden Centre
dispatch in `dispatch/log.md`, staged it, committed it, and then saw the
second line still on your clipboard. The third pallet went out marked
fragile. That was the whole reason the entry needed writing.

It belongs in that commit. Not in a commit after it called "oops",
which is what most records are quietly full of.

So you want the commit undone and the work kept. Those are different
things, and the command that separates them is `reset`.

*`reset` moves a branch label.* That is the whole of it. `main` is a
label pointing at a commit; `git reset <commit>` peels it off and puts
it on a different one. In the warehouse, it takes crates back off the
end of a shelf line. It does not delete commits, and its frightening
reputation comes entirely from one of its three flags.

The flag says what to do with the *files*:

    --soft     leave everything as it is, staged
    --mixed    leave the files, unstage them (the default)
    --hard     make the files match the commit you moved to

One idea with a dial. `--soft` is the gentlest: move the label back one
commit, and everything that commit held is sitting in the staging area,
as though you had just run `git add`.

  try:  git log --oneline
        git show --stat HEAD

One commit, holding both lines. The second is `- Third pallet marked fragile.`
