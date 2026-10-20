from __future__ import annotations

import argparse
from pathlib import Path

from git_tutorial.errors import RepoNotFound
from git_tutorial.session.lifecycle import Session
from git_tutorial.state.store import StateStore


class BindFailure(Exception):
    """Carries the exit code and the message the verb should print."""

    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


def bind_session(args: argparse.Namespace) -> Session:
    """Each way of not being set up gets its own message."""
    from git_tutorial.cli import EXIT_NO_REPO

    repo_path = Path(getattr(args, "repo", None) or Path.cwd())

    try:
        session = Session.open(repo_path=repo_path, levels=getattr(args, "levels", None))
    except RepoNotFound:
        raise BindFailure(
            EXIT_NO_REPO,
            "You are not in a git repository.\n"
            "  Run `wt start` where you want your workspace, then `cd` into it.",
        ) from None

    store = StateStore(session.worktree)
    if not store.exists():
        raise BindFailure(
            EXIT_NO_REPO,
            f"This repository is not a git-tutorial workspace:\n    {session.worktree}\n\n"
            "  `wt start` creates one. If you already have one, cd into it.",
        )

    progress = store.load()
    if progress.current_level_id is None and not progress.completed:
        raise BindFailure(
            EXIT_NO_REPO,
            "This workspace has progress saved but no job in progress.\n"
            "  Run `wt start` to pick up where you left off.",
        )

    return session
