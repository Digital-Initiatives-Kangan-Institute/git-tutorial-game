from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Self

from git_tutorial.errors import LevelAuthoringError
from git_tutorial.git.probe import GitRepoProbe
from git_tutorial.git.runner import GitResult, GitRunner, build_env
from git_tutorial.git.snapshot import RepoSnapshot
from git_tutorial.testing.determinism import CONFIG_ARGS, FixedClock, base_env


class RepoBuilder:
    """Constructs and manipulates a real git repo.

    This is both the test-fixture DSL and the concrete RepoHandle that level
    setup scripts receive. One API, so every level exercises the same code the
    engine's own tests do.
    """

    def __init__(
        self,
        path: Path,
        *,
        home: Path | None = None,
        default_branch: str = "main",
        deterministic: bool = True,
    ) -> None:
        self.path = Path(path)
        self.default_branch = default_branch
        self.deterministic = deterministic
        self.clock = FixedClock()
        self._home = Path(home) if home is not None else self.path.parent / ".fixture-home"
        self._probe: GitRepoProbe | None = None

    # -- plumbing -----------------------------------------------------------

    def _env(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        if not self.deterministic:
            return dict(extra or {})
        self._home.mkdir(parents=True, exist_ok=True)
        env = base_env(str(self._home))
        if extra:
            env.update(extra)
        return env

    def _runner(self, extra_env: dict[str, str] | None = None) -> GitRunner:
        return GitRunner(self.path, env=self._env(extra_env))

    def git(self, *args: str, check: bool = True, _env: dict[str, str] | None = None) -> GitResult:
        config = CONFIG_ARGS if self.deterministic else ()
        return self._runner(_env).run(*config, *args, check=check)

    def raw(self, *args: str) -> GitResult:
        return self.git(*args)

    # -- lifecycle ----------------------------------------------------------

    def init(self) -> Self:
        self.path.mkdir(parents=True, exist_ok=True)
        GitRunner(self.path, env=self._env()).run(
            *CONFIG_ARGS, "init", "-b", self.default_branch, "--object-format=sha1"
        )
        return self

    # -- content ------------------------------------------------------------

    def write(self, rel: str, text: str) -> Self:
        target = self.path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        # newline="" so the text is written verbatim, immune to core.autocrlf.
        with target.open("w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        return self

    def write_file(self, rel: str, text: str) -> Self:
        return self.write(rel, text)

    def delete(self, rel: str) -> Self:
        (self.path / rel).unlink(missing_ok=True)
        return self

    def exists(self, rel: str) -> bool:
        return (self.path / rel).exists()

    def read(self, rel: str) -> str:
        return (self.path / rel).read_text(encoding="utf-8")

    # -- history ------------------------------------------------------------

    def add(self, *paths: str) -> Self:
        self.git("add", "--", *(paths or (".",)))
        return self

    def commit(
        self,
        message: str,
        *,
        add_all: bool = True,
        allow_empty: bool = False,
        date: str | None = None,
        author: tuple[str, str] | None = None,
    ) -> str:
        if add_all:
            self.add()
        args = ["commit", "-m", message]
        if allow_empty:
            args.append("--allow-empty")
        self.git(*args, _env=self._commit_env(date, author))
        return self.git("rev-parse", "HEAD").stdout.strip()

    def _commit_env(
        self, date: str | None, author: tuple[str, str] | None = None
    ) -> dict[str, str] | None:
        """Level setups commit into the student's own repository, where the
        clock is real — so re-running setup would mint a different sha and
        the harness's idempotency check would fail. Pinning the date makes a
        setup that commits as repeatable as one that only edits files.

        `author` is for Act 4, where a commit has to look like somebody
        else's work: a colleague's push the student has to fetch. Without it
        every name in `git log` is the student's own, and the act's whole
        subject is other people.
        """
        env: dict[str, str] = {}
        if date is not None:
            env.update(GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
        elif self.deterministic:
            env.update(self.clock.date_env())
        if author is not None:
            name, email = author
            env.update(
                GIT_AUTHOR_NAME=name, GIT_AUTHOR_EMAIL=email,
                GIT_COMMITTER_NAME=name, GIT_COMMITTER_EMAIL=email,
            )
        return env or None

    def branch(self, name: str, at: str = "HEAD") -> Self:
        self.git("branch", name, at)
        return self

    def branch_at(self, name: str, ref: str) -> Self:
        self.git("branch", "-f", name, ref)
        return self

    def delete_branch(self, name: str, *, force: bool = False, missing_ok: bool = True) -> Self:
        if missing_ok and not self.has_ref(f"refs/heads/{name}"):
            return self
        self.git("branch", "-D" if force else "-d", name)
        return self

    def switch(self, name: str, *, create: bool = False,
               create_if_missing_at: str | None = None) -> Self:
        if create_if_missing_at is not None and not self.has_ref(f"refs/heads/{name}"):
            self.git("switch", "-c", name, create_if_missing_at)
            return self
        args = ["switch"]
        if create:
            args.append("-c")
        args.append(name)
        self.git(*args)
        return self

    def detach(self, rev: str) -> Self:
        self.git("switch", "--detach", rev)
        return self

    def merge(self, other: str, *, ff: bool | None = None, message: str | None = None,
              date: str | None = None) -> Self:
        args = ["merge"]
        if ff is True:
            args.append("--ff-only")
        elif ff is False:
            args.append("--no-ff")
        if message:
            args += ["-m", message]
        self.git(*args, other, _env=self._commit_env(date))
        return self

    def reset(self, rev: str, mode: str = "mixed") -> Self:
        self.git("reset", f"--{mode}", rev)
        return self

    def reset_hard(self, rev: str) -> Self:
        return self.reset(rev, "hard")

    def clean(
        self, *, untracked: bool = True, ignored: bool = False, exclude: Sequence[str] = ()
    ) -> Self:
        if not untracked:
            return self
        args = ["clean", "-fdx" if ignored else "-fd"]
        for pattern in exclude:
            args += ["-e", pattern]
        self.git(*args)
        return self

    def tag(self, name: str, at: str = "HEAD") -> Self:
        self.git("tag", name, at)
        return self

    def tutorial_ref(self, name: str, at: str = "HEAD") -> Self:
        sha = self.git("rev-parse", at).stdout.strip()
        self.git("update-ref", f"refs/tutorial/{name}", sha)
        return self

    def stash(self, *, include_untracked: bool = False) -> Self:
        args = ["stash", "push"]
        if include_untracked:
            args.append("--include-untracked")
        self.git(*args)
        return self

    # -- queries ------------------------------------------------------------

    def has_ref(self, ref: str) -> bool:
        return self.git("rev-parse", "--verify", "--quiet", ref, check=False).ok

    def resolve(self, commit_ref: str) -> str:
        spec = (
            f"refs/tutorial/{commit_ref.removeprefix('tutorial:')}"
            if commit_ref.startswith("tutorial:") else commit_ref
        )
        result = self.git("rev-parse", "--verify", spec, check=False)
        if not result.ok:
            raise LevelAuthoringError(f"could not resolve commit-ref {commit_ref!r}")
        return result.stdout.strip()

    def require_refs(self, *names: str) -> None:
        missing = [n for n in names if not self.has_ref(n if "/" in n else f"refs/tutorial/{n}")]
        if missing:
            raise LevelAuthoringError(
                "missing tutorial refs: "
                + ", ".join(missing)
                + " — the practice history bundle was not unpacked, "
                "or this level's history is not present"
            )

    def reflog_truncate_to(self, offset: int) -> None:
        """Trim .git/logs/HEAD back to a byte offset, on a line boundary.

        Act 3's setups enact a real disaster so the student reads a genuine
        reflog; re-running setup must not append a second copy of it.
        """
        log = self.probe().git_dir / "logs" / "HEAD"
        if not log.exists():
            return
        with log.open("r+b") as handle:
            handle.seek(0)
            data = handle.read(max(offset, 0))
            cut = data.rfind(b"\n")
            handle.seek(0)
            handle.truncate(cut + 1 if cut >= 0 else 0)

    def probe(self) -> GitRepoProbe:
        if self._probe is None:
            self._probe = GitRepoProbe(self.path, GitRunner(self.path, env=self._env()))
        return self._probe

    def snapshot(self) -> RepoSnapshot:
        return self.probe().snapshot()


def isolated_env(home: Path) -> dict[str, str]:
    """A scrubbed environment for tests that shell out without a builder."""
    return build_env(base_env(str(home)))
