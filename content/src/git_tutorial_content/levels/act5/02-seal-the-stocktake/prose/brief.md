Tag the commit "Count aisle B" as `stocktake-march`, and push the tag.

  git log --oneline                     find the hash
  git tag stocktake-march <hash>        tag that commit
  git tag                               list your tags
  git log --oneline --decorate          see the tag beside its commit
  git push origin stocktake-march       send the tag to Head Office

`git tag stocktake-march` with no hash tags `HEAD`, which is the wrong
commit here.
