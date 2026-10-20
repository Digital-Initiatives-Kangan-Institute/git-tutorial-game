You wrote a line in the dispatch log this morning and committed it.
Ines, at Head Office, sent up a new section on damaged stock at about
the same time.

Neither of you did anything wrong, and now there are two `main`s: the
one in your folder and the one at Head Office. They agreed yesterday.
They do not agree now.

    git pull

Pull is taking Head Office's updates, and it is two things you already
know:

    git fetch              read Head Office's bulletin
    git merge origin/main  combine it with what you have

*Pull is fetch and merge in one.* Nothing else. Both sides moved since
they last agreed, so the merge makes a commit with two parents, the
same shape you made when you joined two branches of your own.

What surprises people is the commit they did not write. Pull finishes
the merge itself, with a message git composes, and it sits at the top
of your log. You did make it: `pull` is where you asked.

  try:  git status
        git pull --no-edit
        git log --oneline --graph --all

Ines's section and your log line should both end up on your `main`.
