Pallet wrap is back at 4.20, the two good commits are where they were,
and the history holds both the mistake and the correction.

The two undos, side by side:

  reset    moves a branch label. The history changes shape.
           Safe while the commits are yours alone.

  revert   adds a commit that does the opposite. The history only
           grows. Safe always, including for work Head Office has.

Which to reach for comes down to one question: *has anybody else seen
this commit?* If it has only been on your machine, `reset` is yours. The
moment it has been shared, `revert` is the one that makes no trouble
for anyone else.

`revert` does not delete the commit: `git log` still shows it. And it
is not limited to the newest commit; you just reverted one with two on
top. Next job: what happens when the correction itself was wrong.
