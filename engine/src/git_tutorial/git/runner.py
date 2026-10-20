from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from git_tutorial.errors import GitCommandError

# Applied to every invocation. --no-optional-locks keeps `git status` from
# refreshing the stat cache and colliding with the student's own command.
_GLOBAL_ARGS = (
    "--no-optional-locks",
    "-c",
    "core.quotepath=false",
    "-c",
    "color.ui=false",
    "-c",
    "log.showSignature=false",
)

# Anything that would redirect git at a different repo or config must not leak
# in from the parent environment.
_SCRUBBED = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY")

_FORCED = {
    "LC_ALL": "C",
    "LANG": "C",
    "GIT_TERMINAL_PROMPT": "0",
    "GIT_OPTIONAL_LOCKS": "0",
    "GIT_PAGER": "cat",
    "GIT_ASKPASS": "",
}

_CREATIONFLAGS = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0


@dataclass(frozen=True, slots=True)
class GitResult:
    argv: tuple[str, ...]
    returncode: int
    stdout: str
    stdout_bytes: bytes
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def _decode(raw: bytes) -> str:
    return raw.decode("utf-8", errors="surrogateescape")


def build_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in _SCRUBBED}
    for key in list(env):
        if key.startswith("GIT_CONFIG"):
            del env[key]
    env.update(_FORCED)
    if extra:
        env.update(extra)
    return env


class GitRunner:
    """Runs git as a subprocess with a hygienic, reproducible environment."""

    def __init__(
        self,
        cwd: Path,
        *,
        git_dir: Path | None = None,
        timeout: float = 10.0,
        env: dict[str, str] | None = None,
        git_binary: str = "git",
    ) -> None:
        self.cwd = Path(cwd)
        self.git_dir = git_dir
        self.timeout = timeout
        self.git_binary = git_binary
        self._env = build_env(env)

    def argv(self, *args: str) -> tuple[str, ...]:
        prefix: tuple[str, ...] = (self.git_binary, *_GLOBAL_ARGS, "-C", str(self.cwd))
        if self.git_dir is not None:
            prefix += ("--git-dir", str(self.git_dir))
        return prefix + args

    def run(
        self,
        *args: str,
        check: bool = True,
        stdin: bytes | None = None,
        allow_codes: tuple[int, ...] = (),
        timeout: float | None = None,
    ) -> GitResult:
        argv = self.argv(*args)
        proc = subprocess.run(
            argv,
            capture_output=True,
            input=stdin,
            cwd=str(self.cwd),
            env=self._env,
            timeout=timeout if timeout is not None else self.timeout,
            creationflags=_CREATIONFLAGS,
        )
        result = GitResult(
            argv=argv,
            returncode=proc.returncode,
            stdout=_decode(proc.stdout),
            stdout_bytes=proc.stdout,
            stderr=_decode(proc.stderr),
        )
        if check and not result.ok and result.returncode not in allow_codes:
            raise GitCommandError(args, result.returncode, result.stderr)
        return result

    def popen(self, *args: str) -> subprocess.Popen[bytes]:
        """Long-lived process, for `cat-file --batch`. Caller must close it."""
        return subprocess.Popen(
            self.argv(*args),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(self.cwd),
            env=self._env,
            creationflags=_CREATIONFLAGS,
        )
