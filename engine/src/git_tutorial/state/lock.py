from __future__ import annotations

import time
from pathlib import Path
from types import TracebackType

from git_tutorial.errors import TutorialError

try:  # POSIX
    import fcntl

    _HAVE_FCNTL = True
except ImportError:  # Windows
    _HAVE_FCNTL = False

try:
    import msvcrt

    _HAVE_MSVCRT = True
except ImportError:
    _HAVE_MSVCRT = False


class StateLockTimeout(TutorialError):
    pass


class FileLock:
    """Advisory lock around a progress file.

    `wt answer` in the terminal while `wt` serves the browser is the expected
    workflow, not an edge case, so every read-modify-write takes this.
    """

    def __init__(self, path: Path, *, timeout: float = 2.0, poll: float = 0.05) -> None:
        self.path = path
        self.timeout = timeout
        self.poll = poll
        self._handle: object | None = None

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = self.path.open("a+b")
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                self._try_lock(handle)
            except OSError:
                if time.monotonic() >= deadline:
                    handle.close()
                    raise StateLockTimeout(
                        f"another gq command is using this repo's progress file "
                        f"({self.path}). Is `wt` busy in another window?"
                    ) from None
                time.sleep(self.poll)
            else:
                self._handle = handle
                return

    @staticmethod
    def _try_lock(handle: object) -> None:
        if _HAVE_FCNTL:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)  # type: ignore[attr-defined]
        elif _HAVE_MSVCRT:
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)  # type: ignore[attr-defined]

    def release(self) -> None:
        handle = self._handle
        if handle is None:
            return
        self._handle = None
        try:
            if _HAVE_FCNTL:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)  # type: ignore[attr-defined]
            elif _HAVE_MSVCRT:
                handle.seek(0)  # type: ignore[attr-defined]
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)  # type: ignore[attr-defined]
        finally:
            handle.close()  # type: ignore[attr-defined]

    def __enter__(self) -> FileLock:
        self.acquire()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.release()
