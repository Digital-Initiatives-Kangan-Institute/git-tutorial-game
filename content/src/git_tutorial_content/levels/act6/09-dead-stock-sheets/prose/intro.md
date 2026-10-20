Ines again. Two sheets are going: the aisle E overflow racking came
down after Easter, and Kestrelby have discontinued the seasonal twine.
I have retired both sheets at Head Office.

You counted both this morning and committed the counts, so your pull
will stop twice, on two modify/delete conflicts. You know the answer to
those: `git rm`, once for each.

While you are there, look at what else that commit picked up.
`stocktake.tmp` is the scanner's scratch dump. It is useful to have on
disk, and it was never meant to be a record. Somebody ran `git add .`.

Taking it off the books without deleting it is a different form of the
same command:

    git rm <path>            delete the file, and stage the deletion
    git rm --cached <path>   stage the deletion, keep the file on disk

After `--cached`, the file is untracked: still there, and no longer in
the next commit. Add it to `.gitignore` as well, or `git status` will
keep listing it and the next `git add .` will put it straight back.

  try:  git pull
        git status
        git rm --cached stocktake.tmp

Ines
