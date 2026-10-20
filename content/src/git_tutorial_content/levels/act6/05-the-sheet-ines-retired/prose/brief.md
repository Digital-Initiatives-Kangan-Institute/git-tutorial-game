Pull, agree with Ines's deletion, push.

  git pull                       stops: modify/delete
  git status                     "deleted by them"
  git rm docs/opening-checks.md  delete the file and stage the deletion
  git commit --no-edit           finish the merge
  git push

`git rm <path>` is a plain delete plus `git add`, in one step. Keeping
the file instead (`git add` it) would bring back a sheet Head Office
has retired.
