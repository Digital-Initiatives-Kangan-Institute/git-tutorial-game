The rush note went up as its own commit, and the count was settled
after, in a merge of its own.

`git merge --abort` is not giving up. It is "not now". A paused merge
holds the repository in a state where the next commit means something
special, and when something else needs doing first, the clean move is
to step out, do it, and step back in. The disagreement waits for you:
the second pull stopped in exactly the same place.

Next job: a sheet you deleted, and Head Office did not.
