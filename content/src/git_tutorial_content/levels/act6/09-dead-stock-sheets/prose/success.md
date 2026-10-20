Both sheets are gone, and `stocktake.tmp` is still on disk, untracked
and ignored.

`git rm` and `git rm --cached` differ by one word and one consequence:
whether the file survives on disk. Retired records should go entirely.
A file that was only ever local, a scratch dump or a log, should stay
where it is and simply stop being tracked, and `.gitignore` keeps it
that way.

Last job of the week: Marta signs off the stocktake, and everything
you have learned this act arrives in one pull.
