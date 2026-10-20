from __future__ import annotations

import contextlib
import json
import os
import tempfile
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from git_tutorial.state import paths
from git_tutorial.state.lock import FileLock
from git_tutorial.state.migrations import migrate
from git_tutorial.state.models import CursorFile, Progress


def _write_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, sort_keys=False) + "\n"

    # delete=False because the file is renamed into place, not closed away.
    handle = tempfile.NamedTemporaryFile(  # noqa: SIM115
        mode="w", encoding="utf-8", dir=str(path.parent), prefix=path.name + ".", suffix=".tmp",
        delete=False, newline="",
    )
    tmp = Path(handle.name)
    try:
        with handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


class StateStore:
    """Progress for one bound repository.

    Lives under ~/.gittutorial, never inside the student's repo: Act 3 has them
    running `reset --hard` and deleting refs, and state in the working tree
    would be destroyed by the very lessons the game is teaching.
    """

    def __init__(self, worktree: Path) -> None:
        self.worktree = Path(worktree)
        self.recovered_from_corruption = False

    @property
    def directory(self) -> Path:
        return paths.repo_dir(self.worktree)

    @property
    def progress_path(self) -> Path:
        return paths.progress_file(self.worktree)

    @property
    def cursors_path(self) -> Path:
        return paths.cursors_file(self.worktree)

    def exists(self) -> bool:
        return self.progress_path.exists()

    def load(self) -> Progress:
        path = self.progress_path
        if not path.exists():
            return Progress(repo_path=str(self.worktree))
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self._quarantine(path)
            return Progress(repo_path=str(self.worktree))

        if not isinstance(raw, dict):
            self._quarantine(path)
            return Progress(repo_path=str(self.worktree))

        return Progress.from_dict(migrate(raw))

    def _quarantine(self, path: Path) -> None:
        """Never refuse to run because of a damaged progress file.

        Losing progress is bad. Being unable to play at 11pm with no
        instructor to ask is worse.
        """
        backup = path.with_suffix(f".json.corrupt-{int(time.time())}")
        with contextlib.suppress(OSError):
            path.replace(backup)
        self.recovered_from_corruption = True

    def save(self, progress: Progress) -> None:
        progress.updated_at = time.time()
        if not progress.created_at:
            progress.created_at = progress.updated_at
        if not progress.repo_path:
            progress.repo_path = str(self.worktree)
        _write_atomic(self.progress_path, progress.to_dict())

    @contextmanager
    def mutate(self) -> Iterator[Progress]:
        with FileLock(self.directory / ".lock"):
            progress = self.load()
            yield progress
            self.save(progress)

    def load_cursors(self) -> CursorFile:
        path = self.cursors_path
        if not path.exists():
            return CursorFile()
        try:
            return CursorFile.from_dict(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            return CursorFile()

    def save_cursors(self, cursors: CursorFile) -> None:
        _write_atomic(self.cursors_path, cursors.to_dict())
