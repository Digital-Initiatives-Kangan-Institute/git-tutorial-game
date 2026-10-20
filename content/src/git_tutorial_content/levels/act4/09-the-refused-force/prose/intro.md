You drafted the stocktake plan yesterday and pushed it. This morning
you reworded the commit message, with `reset --soft` and a fresh
commit, because "Draft the stocktake plan" did not say which
stocktake.

That rewrite made a *different commit*: same file, new hash. Head
Office still has the old one, so `git push` is refused for the reason
you already know. The branch there cannot move forwards to a commit
that does not contain what it has.

This time you do not want to pull their copy in under yours. You want
your version of your own commit to replace the one you sent up. That is
what forcing is for:

    git push --force              replace whatever Head Office has
    git push --force-with-lease   replace it, but only if it is as I
                                  last saw it

Use the second. Always. `--force` does what you said, and anything
anyone else sent up in the meantime stops being reachable.
`--force-with-lease` first checks that the remote branch is still where
your last fetch saw it. If someone has pushed since, git refuses with
`stale info` rather than destroying work you did not know existed.

  try:  git log --oneline -n 2
        git push --force-with-lease

The refusal is the thing to read.
