Accepted. Both commits are at Head Office, joined by the merge you made
by pulling.

The rule underneath the message: a branch on a remote may only move
forwards. Your push asked it to move to a commit that did not contain
what was there, and git refused rather than orphan Ines's work.

So pull before you push. You will still be refused now and then, when
someone sends records up in the seconds between, and the answer is the
same every time: pull, then push again. Next job: look before you
take the updates in.
