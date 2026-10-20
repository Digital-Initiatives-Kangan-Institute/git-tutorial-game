Ines here again. I have retired the opening checks sheet. Those checks
are in Head Office's site handbook now, for every depot at once, and
two copies of a safety check is one too many. I took the link out of
the README as well.

I hear you added the first-aid box to the sheet this morning. Thank
you: I have put it in the handbook. But the sheet itself is going.

So far every conflict has been two versions of the same lines. This
one is different. You changed a file; Head Office deleted it. When you
pull, git reports:

    CONFLICT (modify/delete): docs/opening-checks.md deleted in ...
    and modified in HEAD.

There are no markers in the file, because there is only one version of
it. `git status` lists it as "deleted by them", and the browser shows
the same. Git leaves your copy on disk so you can choose.

To take the sheet off the books, use *git rm*: it deletes the file and
stages the deletion in one step. Staging it settles the conflict, the
same way `git add` does for an edited file.

  try:  git pull
        git status
        git rm docs/opening-checks.md

Then commit and push.
