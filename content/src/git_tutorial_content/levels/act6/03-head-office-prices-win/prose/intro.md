Ines here, from Head Office. The April price list from Kestrelby went
up first thing. I gather you had already pencilled in the prices their
rep gave you on the phone, and committed them along with a note in the
dispatch log.

Thank you, but on prices Head Office's list is the one that stands,
every line of it. When you pull, the price list will be held at
inspection, and there is nothing in it to weigh up: my version wins
whole.

You could edit out each block by hand, but that is slow and it is how
typos get in. Git can hand you one side of a file whole:

    git restore --theirs <path>   Head Office's version, no markers
    git restore --ours <path>     your version, no markers

In a pull, *ours* is your side (what you had committed) and *theirs* is
what came from Head Office. Your count, their count. Restoring a side
only rewrites the file in the working tree. You still `git add` it to
say it is settled, and commit to finish the merge.

It works on one file at a time. Your dispatch log line is not in
conflict and stays exactly as you wrote it.

  try:  git pull
        git status
        git restore --theirs suppliers/price-list.md

Ines
