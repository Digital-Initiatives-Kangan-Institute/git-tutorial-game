Merge the finished branch into `main`, push, then delete the branch in
both places.

  git switch main
  git pull
  git merge aisle-e-fitout
  git push
  git branch -d aisle-e-fitout
  git push origin --delete aisle-e-fitout
  git branch -a                  only main and origin/main left

Merge and push first. Delete last.
