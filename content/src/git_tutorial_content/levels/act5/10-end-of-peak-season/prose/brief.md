Merge, push, tag, push the tag, then delete the branch in both places.

  git switch main
  git pull                               Theo's commit arrives
  git merge --no-edit peak-close
  git push
  git tag peak-2025                      tags HEAD, the merge
  git push origin peak-2025
  git branch -d peak-close
  git push origin --delete peak-close
  git log --oneline --graph --decorate --all -n 6

Tag after pushing `main`, so the seal is on the commit Head Office has.
