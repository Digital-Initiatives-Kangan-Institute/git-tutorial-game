Pull, take Head Office's price list whole, keep your log line, push.

  git pull                                     it stops on the price list
  git restore --theirs suppliers/price-list.md Head Office's version
  git diff origin/main -- suppliers/price-list.md   should print nothing
  git add suppliers/price-list.md              settled
  git commit --no-edit                         finish the merge
  git push

In a pull, `--ours` is your committed side and `--theirs` is Head
Office's. Neither one stages anything: `git add` still says "settled".
