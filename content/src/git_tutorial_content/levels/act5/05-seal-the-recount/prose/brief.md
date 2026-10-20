Commit Theo's recount on `main`, push it, tag it, push the tag.

  git diff                       Theo's change: 36 rolls, not 40
  git add stock/aisle-b.md
  git commit -m "Recount B-14 pallet wrap"
  git push                       sends the commit, not tags
  git tag recount-b14            tags HEAD
  git push origin recount-b14    sends the tag
  git ls-remote --tags origin    what Head Office holds

Tag after committing: a tag made first would seal the old count.
