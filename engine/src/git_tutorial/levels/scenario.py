"""The public contract level authors write against.

Removing anything here, or changing a signature, breaks every published
level pack and needs LEVEL_FORMAT_VERSION bumped. Adding a method, or a
keyword argument with a default, does not.

`commit` and `read` were used by every act's setups for a year before they
were written down here, which is the usual way a contract rots: the pack
and the engine ship together, so nothing complained.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol, Self, runtime_checkable


@runtime_checkable
class RepoHandle(Protocol):
    """What a level's setup() may do to the practice repo."""

    def git(self, *args: str, check: bool = True) -> Any: ...

    def switch(
        self, name: str, *, create: bool = False, create_if_missing_at: str | None = None
    ) -> Self: ...

    def reset_hard(self, rev: str) -> Self: ...

    def clean(self, *, untracked: bool = True, ignored: bool = False) -> Self: ...

    def delete_branch(
        self, name: str, *, force: bool = False, missing_ok: bool = True
    ) -> Self: ...

    def branch_at(self, name: str, ref: str) -> Self: ...

    def write_file(self, rel: str, text: str) -> Self: ...

    def read(self, rel: str) -> str: ...

    # `author` makes a commit look like a colleague's, which is what Act 4
    # needs to manufacture anything worth fetching. `date` pins the sha so a
    # setup that commits is still idempotent.
    def commit(
        self,
        message: str,
        *,
        add_all: bool = True,
        allow_empty: bool = False,
        date: str | None = None,
        author: tuple[str, str] | None = None,
    ) -> str: ...

    def exists(self, rel: str) -> bool: ...

    def has_ref(self, ref: str) -> bool: ...

    def require_refs(self, *names: str) -> None: ...

    def reflog_truncate_to(self, offset: int) -> None: ...

    def resolve(self, commit_ref: str) -> str: ...


@dataclass
class LevelState:
    """What a level's setup() may know about the attempt in progress."""

    level_id: str
    start_head: str = ""
    start_time: float = 0.0
    reflog_offset_at_level_start: int = 0
    attempt: int = 1
    solved_before: bool = False
    hints_shown: list[int] = field(default_factory=list)
    reset_count: int = 0
    extra_worktree_paths: list[str] = field(default_factory=list)

    def snapshot_worktree(self, paths: Sequence[str]) -> None:
        """Ask for these paths to be fingerprinted as the level's baseline.

        Paths named by a `worktree_unchanged` assertion are captured
        automatically, so this is only needed for anything beyond those.
        """
        for path in paths:
            if path not in self.extra_worktree_paths:
                self.extra_worktree_paths.append(path)


SetupFn = Callable[[RepoHandle, LevelState], None]
