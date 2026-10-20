`main` and `origin/main` agree, and the history is a straight line:
pull made no merge commit because there was nothing to merge.

  nothing of your own     pull fast-forwards. Straight line.
  commits on both sides   pull merges. Merge commit.
  push without pulling    refused: the branch cannot move forwards.

Pull when you start, commit as you go, pull again before you push, and
push before you walk away. Next job: a force push that git refuses.
