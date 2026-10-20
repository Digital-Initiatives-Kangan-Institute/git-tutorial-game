Pull, bring back Ines's receiving sheet whole, push.

  git pull                                  stops: deleted by us
  git status
  git restore --theirs docs/receiving.md    Head Office's version
  git add docs/receiving.md                 keep it: settled
  git commit --no-edit
  git push

For a deleted file, `git add` keeps it and `git rm` agrees it is gone.
