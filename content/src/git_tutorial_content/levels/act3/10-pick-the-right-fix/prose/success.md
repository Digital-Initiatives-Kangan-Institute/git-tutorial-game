Three kinds of wrong, three tools, nothing lost that anybody wanted.

That is the act. The commands were only ever the vocabulary; the skill
is the question you asked three times just now, *how far has this
got?*, because it decides everything else.

  restore    working tree back to the last commit. No history touched.
  reset      moves a branch label. The commits stay, out in the yard,
             until git's housekeeping comes round.
  revert     adds a commit undoing an older one. History only grows.
  reflog     the gate log: every position HEAD has held.
  ORIG_HEAD  where you were before the last big move. The quick undo.

And one rule that outranks all of it: *anything committed can be
recovered; anything uncommitted cannot.* Every rescue in this act
started from a commit. Commit early, commit messily, tidy afterwards.

Next act, Head Office: everything you have learned about rewriting
history gets one new condition, whether anybody else has seen it.
