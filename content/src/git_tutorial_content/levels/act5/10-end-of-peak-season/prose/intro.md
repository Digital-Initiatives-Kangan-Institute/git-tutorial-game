Easter is over. The overflow racking is coming down, Sunday opening
ends this week, and you wrote the close-down notes yesterday on
`peak-close`. They are at Head Office already.

Marta wants the season closed properly: your notes in `main`, the end
of the season sealed as `peak-2025` so next year's planning can start
from it, and no branches left lying about.

Every command this takes, you have used this act. What is new is doing
them in one go, in an order that is safe at every step:

    git switch main              merge from the receiving branch
    git pull                     Theo sent something up this morning
    git merge peak-close         fold your notes in on top of his
    git push                     main is safe at Head Office
    git tag peak-2025            seal the commit Head Office now has
    git push origin peak-2025    and send the seal
    git branch -d peak-close     take the branch down here
    git push origin --delete peak-close   and at Head Office

Each step only happens once the one before it is safe.

  try:  git status
        git fetch --prune
        git log --oneline --graph --all -n 6

Close the season.
