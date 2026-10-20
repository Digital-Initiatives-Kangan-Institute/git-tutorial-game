from __future__ import annotations

import subprocess
from types import TracebackType

from git_tutorial.git.runner import GitRunner


class BlobReader:
    """Lazy blob content over one persistent `cat-file --batch`.

    Content is deliberately absent from RepoSnapshot: content predicates touch
    a handful of paths, and hashing whole trees into every 1Hz snapshot would
    dominate the tick cost.
    """

    def __init__(self, runner: GitRunner) -> None:
        self._runner = runner
        self._cache: dict[str, bytes | None] = {}
        self._proc: subprocess.Popen[bytes] | None = None

    @property
    def runner(self) -> GitRunner:
        """For the few predicates that must look beyond this repository."""
        return self._runner

    def _ensure(self) -> None:
        if self._proc is None:
            self._proc = self._runner.popen("cat-file", "--batch")

    def read(self, spec: str) -> bytes | None:
        """Returns the object's bytes, or None if it does not exist."""
        if spec in self._cache:
            return self._cache[spec]
        self._ensure()
        proc = self._proc
        assert proc is not None and proc.stdin is not None and proc.stdout is not None

        proc.stdin.write(spec.encode("utf-8", errors="surrogateescape") + b"\n")
        proc.stdin.flush()

        header = proc.stdout.readline().decode("utf-8", errors="surrogateescape").strip()
        if not header or header.endswith((" missing", " ambiguous")):
            self._cache[spec] = None
            return None

        _sha, _objtype, size_raw = header.rsplit(" ", 2)
        payload: bytes = proc.stdout.read(int(size_raw))
        proc.stdout.read(1)  # trailing newline
        self._cache[spec] = payload
        return payload

    def read_text(self, spec: str) -> str | None:
        raw = self.read(spec)
        return None if raw is None else raw.decode("utf-8", errors="surrogateescape")

    def read_worktree(self, path: str) -> str | None:
        """Reads a working-tree file from disk.

        Worktree blob hashes come from `hash-object` without -w, so those
        objects are not in the database and cat-file cannot see them. Writing
        them just to read them would mean the probe mutates the student's repo,
        which it must never do.
        """
        try:
            return (self._runner.cwd / path).read_text(encoding="utf-8", errors="surrogateescape")
        except OSError:
            return None

    def close(self) -> None:
        if self._proc is not None:
            proc, self._proc = self._proc, None
            if proc.stdin is not None:
                proc.stdin.close()
            proc.wait(timeout=5)

    def __enter__(self) -> BlobReader:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()
