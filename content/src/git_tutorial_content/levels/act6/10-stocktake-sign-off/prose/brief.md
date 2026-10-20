Pull, settle three conflicts three ways, push, tag, push the tag.

  git pull                                     stops on three files
  git status                                   each file and its kind
  git log --merge --oneline                    both sides' commits
  git add stock/aisle-b.md                     after editing it
  git restore --theirs suppliers/price-list.md
  git add suppliers/price-list.md
  git rm docs/stocktake-checklist.md
  git commit --no-edit                         finish the merge
  git push
  git tag stocktake-final
  git push origin stocktake-final

`stock/aisle-b.md` should end up with:

    38 rolls counted.        (B-14, Theo's)
    26 bundles counted.      (B-15, yours)

Tag after pushing, so the tag is on the commit Head Office has.
