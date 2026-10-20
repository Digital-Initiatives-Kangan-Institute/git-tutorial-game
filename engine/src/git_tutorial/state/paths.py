from __future__ import annotations

import hashlib
import os
from pathlib import Path

ENV_HOME = "GITTUTORIAL_HOME"
ENV_LEVELS = "GITTUTORIAL_LEVELS"
ENV_ANSWERS = "GITTUTORIAL_ANSWERS"


def home() -> Path:
    override = os.environ.get(ENV_HOME)
    root = Path(override) if override else Path.home() / ".gittutorial"
    return root.expanduser()


def ensure_home() -> Path:
    root = home()
    root.mkdir(parents=True, exist_ok=True)
    return root


def head_office_dir() -> Path:
    """The bare repository that plays Head Office: the workspace's origin."""
    return home() / "head-office.git"


def levels_clone_dir() -> Path:
    return home() / "levels"


def cache_dir() -> Path:
    return home() / "cache"


def repo_key(worktree: Path) -> str:
    """Stable per-repo key.

    Computed from the realpath so a student working in a subdirectory, or
    through a symlink, binds to the same progress. normcase because macOS and
    Windows are case-insensitive. The basename prefix is for humans reading
    ~/.gittutorial/repos/.
    """
    real = os.path.normcase(os.path.realpath(str(worktree)))
    digest = hashlib.sha256(real.encode("utf-8", errors="surrogateescape")).hexdigest()[:12]
    name = Path(real).name or "repo"
    return f"{name}-{digest}"


def repo_dir(worktree: Path) -> Path:
    return home() / "repos" / repo_key(worktree)


def progress_file(worktree: Path) -> Path:
    return repo_dir(worktree) / "progress.json"


def cursors_file(worktree: Path) -> Path:
    """Separate from progress.json on purpose.

    M3's reflog tail rewrites cursors at 1Hz while progress changes rarely;
    sharing a file would mean taking the progress lock on every tick.
    """
    return repo_dir(worktree) / "cursors.json"
