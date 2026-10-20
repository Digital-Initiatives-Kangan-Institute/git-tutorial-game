Clear the `origin/*` names for branches Head Office has deleted.

  git branch -r        your notes of Head Office's branches
  git fetch            updates and adds notes; never removes one
  git fetch --prune    also removes notes for deleted branches
  git branch -r        what is really left

`git fetch --prune` prints `- [deleted]` for each name it removes.
Your own branches and commits are never touched.
