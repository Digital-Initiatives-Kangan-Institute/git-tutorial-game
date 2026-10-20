The aisle E racking is in, fitted and load-checked, and your notes on
the fit-out are on `aisle-e-fitout`, already sent up to Head Office.

Ines is buried in Easter orders. "It's yours," she says. "Fold it into
main yourself and clear the branch away when it's in."

That is the same tidy-up as the rota, with the merge done by you
instead of for you. The order is the whole job:

    git switch main                         merge from the receiving branch
    git pull                                in case Head Office has moved
    git merge aisle-e-fitout                fold the work in
    git push                                and send main up
    git branch -d aisle-e-fitout            then delete your branch
    git push origin --delete aisle-e-fitout and Head Office's

Delete before merging and the fit-out notes are on no branch at all.
The commits would still exist for a while, but nothing would point at
them: a crate left in the yard.

  try:  git status
        git log --oneline --graph --all

Merge, push, and only then delete.
