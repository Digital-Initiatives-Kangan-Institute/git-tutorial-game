Three commits, three files, exactly as they were before the slip.

Two names worth keeping, and they do different jobs:

  ORIG_HEAD   where you were before the last big move. One position.
              The undo for the thing you just did.

  reflog      every position HEAD has held, with what moved it.
              The history, when "the thing you just did" was four
              things ago.

What `--hard` does to *commits* is nothing at all: the label moves, the
commits stay, and ten seconds with `ORIG_HEAD` undoes it.

What it does to *uncommitted* work is different, and this is the one
sharp edge in the act. `--hard` makes your files match the commit, and
a change you had not committed has no commit to be found in. No reflog
line, no `ORIG_HEAD`. Gone.

  commit early, even messily. A commit is recoverable;
  an unsaved change is not.

Next job: a mistake somebody else already has.
