from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from git_tutorial.errors import GitCommandError, RepoNotFound
from git_tutorial.git.runner import GitRunner


@dataclass(frozen=True, slots=True)
class RepoLocation:
    worktree: Path
    git_dir: Path


def discover(start: Path, runner: GitRunner | None = None) -> RepoLocation:
    """Resolves the worktree root and git dir once, so ticks never re-pay for it.

    --absolute-git-dir handles the `.git`-as-a-file case (worktrees, submodules)
    that a naive `start / ".git"` would get wrong.
    """
    start = Path(start).resolve()
    runner = runner or GitRunner(start)
    try:
        result = runner.run("rev-parse", "--absolute-git-dir", "--show-toplevel")
    except GitCommandError as exc:
        raise RepoNotFound(f"{start} is not inside a git repository") from exc

    lines = result.stdout.splitlines()
    if len(lines) < 2:
        raise RepoNotFound(f"could not resolve a repository at {start}")
    return RepoLocation(worktree=Path(lines[1]), git_dir=Path(lines[0]))
