Merge `aisle-d-signoff` into `main`. Two files conflict, and both have
to be settled before the merge can be committed.

  git merge aisle-d-signoff   start it
  git status                  which files are still unresolved
  git add <path>              this one is settled
  git commit --no-edit        only works when the list is empty

What each file wants:

  dispatch/log.md   keep both entries, one per line
  README.md         one line covering both. It has to contain the exact
                    phrase `gate 2 or in aisle D`: the check looks for
                    it, so this part is a requirement, not a judgement

Keep the yard phone number on that line. Delete every `<<<<<<<`,
`=======` and `>>>>>>>` line in both files.
