Tuesday of stocktake week. Before nine you had committed two things:
your B-14 count, and the pallet wrap price Kestrelby's rep quoted you
on the phone. Meanwhile Theo sent up his B-14 count and Ines sent up
Head Office's April price list.

This pull is going to stop in more than one place. The temptation is
to open the first file and start deleting markers. Marta's rule is the
opposite: read the whole inspection report before you touch anything.

Three questions, three commands:

    git status                  which files are held ("Unmerged paths")
    grep -c '^<<<<<<<' <file>   how many blocks in one file
    git log --merge --oneline   which commits, on both sides, disagree

*git log --merge* only works while a merge is stopped. It lists the
commits from your side and from Head Office's side that touched the
conflicted files, and nothing else: the two sets of delivery notes that
disagree, side by side. The browser shows the same files with their
block counts.

Then settle it with Marta's rule: counts are whoever counted on the
floor, so B-14 is your 39. Prices are Head Office's, so take Ines's
lines in the price list.

  try:  git pull
        git status
        git log --merge --oneline

Answer the three questions first, then resolve both files and push.
