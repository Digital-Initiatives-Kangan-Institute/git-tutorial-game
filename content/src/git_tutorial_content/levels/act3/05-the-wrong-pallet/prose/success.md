The README link is in, your notes are not, and they are still in the
folder where you left them.

The three flags, now that you have used two of them:

    --soft    label moves. Files and staging untouched.
    --mixed   label moves. Files untouched, staging emptied.
    --hard    label moves. Files and staging made to match.

Same command, one dial: how much of what you have should follow the
label. The only thing that changed between the last job and this one is
the staging area.

A note on the file that should never have been there. It is out of the
commit you were about to build on, which is the case that matters
today. If a file like that has already gone up to Head Office, taking
it out of your next commit does not take it out of the history they
hold. The real lesson is Act 1's: `.gitignore` the thing before
`add .` can find it.

And `git status` before `git commit` is the habit that makes this whole
job unnecessary. Next: the slip everyone makes with `--hard`.
