from __future__ import annotations

import importlib.util
import re
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from git_tutorial.errors import LevelAuthoringError, TutorialError
from git_tutorial.levels.model import Level
from git_tutorial.levels.scenario import LevelState, RepoHandle, SetupFn

SETUP_FUNCTION = "setup"


class LevelSetupError(LevelAuthoringError):
    def __init__(self, level_id: str, script: Path, message: str) -> None:
        self.level_id = level_id
        self.script = script
        super().__init__(message)


@contextmanager
def _importable(root: Path | None) -> Iterator[None]:
    """Put the pack root on sys.path so a shared helpers.py works.

    Without this, a pip-installed pack (where the package is importable) and a
    git-clone pack at ~/.gittutorial/levels behave differently — exactly the
    divergence that breaks a whole cohort.
    """
    if root is None:
        yield
        return
    entry = str(root)
    added = entry not in sys.path
    if added:
        sys.path.insert(0, entry)
    try:
        yield
    finally:
        if added and sys.path and sys.path[0] == entry:
            sys.path.pop(0)


def _module_name(level_id: str) -> str:
    return "git_tutorial_level_" + re.sub(r"\W", "_", level_id)


def load_setup(level: Level, *, pack_root: Path | None = None) -> SetupFn:
    script = level.directory / (level.setup or "setup.py")
    if not script.exists():
        raise LevelSetupError(level.id, script, f"no setup script at {script}")

    # Namespaced, and registered before exec: every level's script is called
    # setup.py, so unnamespaced they collide, and without pre-registration a
    # script defining a class breaks and tracebacks lose their source lines.
    name = _module_name(level.id)
    spec = importlib.util.spec_from_file_location(name, script)
    if spec is None or spec.loader is None:
        raise LevelSetupError(level.id, script, f"could not load {script}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        with _importable(pack_root):
            spec.loader.exec_module(module)
    except TutorialError:
        sys.modules.pop(name, None)
        raise
    except Exception as exc:
        sys.modules.pop(name, None)
        raise LevelSetupError(level.id, script, f"{type(exc).__name__}: {exc}") from exc

    fn = getattr(module, SETUP_FUNCTION, None)
    if fn is None:
        raise LevelSetupError(level.id, script, f"{script.name} defines no {SETUP_FUNCTION}()")
    if not callable(fn):
        raise LevelSetupError(
            level.id, script, f"{SETUP_FUNCTION} in {script.name} is not callable"
        )
    return fn  # type: ignore[no-any-return]


def run_setup(
    level: Level, repo: RepoHandle, state: LevelState, *, pack_root: Path | None = None
) -> None:
    """Re-exec the script every time.

    Caching costs milliseconds saved against a whole class of stale-module bug
    during authoring, where `wt reset` in a loop is the primary workflow.
    """
    script = level.directory / (level.setup or "setup.py")
    fn = load_setup(level, pack_root=pack_root)
    try:
        with _importable(pack_root):
            fn(repo, state)
    except TutorialError as exc:
        raise LevelSetupError(level.id, script, str(exc)) from exc
    except Exception as exc:
        raise LevelSetupError(level.id, script, f"{type(exc).__name__}: {exc}") from exc
