Theo spent Wednesday morning typing up last week's paper count of
aisle B and sent it up, with a line in the dispatch log to say so.

You spent the same morning walking aisle B with the scanner, and
committed what it read. Yours is a week newer. Marta has no doubt about
which count stands: the scan.

So when you pull and the stock sheet is held, the decision is already
made, and it is your side whole. Last job you met the pair:

    git restore --theirs <path>   Head Office's version
    git restore --ours <path>     your version

*Ours* is the commit you were on when you pulled: your scan. Your count
beats their count, for this one file. Theo's line in the dispatch log
is not in conflict, so it comes in either way, and it should.

  try:  git pull
        git status
        git diff

Keep your scan, keep Theo's log line, and push.
