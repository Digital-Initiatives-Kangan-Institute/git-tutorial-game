from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from git_tutorial.git.graph import CommitGraph
from git_tutorial.git.status_parse import StatusEntry

# Markers under .git that mean an operation is paused mid-flight (spec 5.2).
# ORIG_HEAD is not an in-progress marker; it is the built-in undo pointer, and
# it is carried in special_refs instead.
IN_PROGRESS_FILES = ("MERGE_HEAD", "MERGE_MSG", "CHERRY_PICK_HEAD", "REVERT_HEAD")
IN_PROGRESS_DIRS = ("rebase-merge", "rebase-apply")

# Read directly so their sha is resolvable as a commit-ref (spec 6.2).
SPECIAL_REF_FILES = ("ORIG_HEAD", "MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD")


@dataclass(frozen=True, slots=True)
class RepoSnapshot:
    head_ref: str | None  # None => detached
    head_sha: str
    branches: Mapping[str, str]
    tags: Mapping[str, str]
    tutorial_refs: Mapping[str, str]
    remote_refs: Mapping[str, str]
    special_refs: Mapping[str, str]
    upstream: Mapping[str, str]
    ahead_behind: tuple[int, int] | None
    status: tuple[StatusEntry, ...]
    graph: CommitGraph
    in_progress: frozenset[str]
    stash_count: int
    index_blobs: Mapping[str, str]
    worktree_blobs: Mapping[str, str]
    taken_at: float

    @property
    def detached(self) -> bool:
        return self.head_ref is None

    @property
    def is_clean(self) -> bool:
        return not any(e.kind != "untracked" and e.kind != "ignored" for e in self.status)

    def tips(self) -> dict[str, str]:
        """Every ref a graph walk should start from."""
        tips: dict[str, str] = {}
        tips.update({f"refs/heads/{k}": v for k, v in self.branches.items()})
        tips.update({f"refs/remotes/{k}": v for k, v in self.remote_refs.items()})
        tips.update({f"refs/tutorial/{k}": v for k, v in self.tutorial_refs.items()})
        if self.head_sha:
            tips["HEAD"] = self.head_sha
        return tips
