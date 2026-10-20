Ines at Head Office sent up a change to the supplier price list twenty
minutes ago.

Your repository has no idea. `git log` shows what it showed yesterday,
`git status` says nothing unusual, and every file is as you left it. A
clone does not listen for news. It finds out when you ask.

    git fetch

Fetch is reading Head Office's bulletin. It goes to the remote, brings
back every commit you do not have, and stops. Your branches do not
move. No file in your folder changes.

The news goes under a name of its own, `origin/main`. That is a
*remote-tracking branch*: your record of where `main` was at Head
Office the last time you looked. You cannot commit to it. It is a note
saying "this is what they had".

So after a fetch you have two names that disagree on purpose:

    main          where your work is
    origin/main   where Head Office's work is

`git status` then says *behind* when Head Office has commits you do
not, and *ahead* when you have commits it does not.

  try:  git fetch
        git status
        git log --oneline --graph --all

Read what arrived, and leave your own `main` alone.
