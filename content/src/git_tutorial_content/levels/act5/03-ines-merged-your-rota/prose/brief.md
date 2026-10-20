The work is merged at Head Office. Bring the merge in, then delete the
branch in both places.

  git switch main                      you cannot delete the branch you are on
  git pull                             Ines's merge commit arrives
  git log --oneline --graph --all
  git branch -d peak-rota              delete your branch; refuses if its work is not safe
  git push origin --delete peak-rota   delete Head Office's branch
  git branch -a                        what is left, here and at origin

Do not reach for `git branch -D`. It deletes without checking, which is
exactly the check you want here.
