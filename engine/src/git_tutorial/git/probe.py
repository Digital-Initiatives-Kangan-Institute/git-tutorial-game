from __future__ import annotations

import time
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from git_tutorial.git import reflog
from git_tutorial.git.blobs import BlobReader
from git_tutorial.git.discovery import RepoLocation, discover
from git_tutorial.git.graph import parse_rev_list
from git_tutorial.git.reflog import GitEvent
from git_tutorial.git.refs_parse import REF_FORMAT, REF_NAMESPACES, parse_for_each_ref
from git_tutorial.git.runner import GitRunner
from git_tutorial.git.snapshot import (
    IN_PROGRESS_DIRS,
    IN_PROGRESS_FILES,
    SPECIAL_REF_FILES,
    RepoSnapshot,
)
from git_tutorial.git.status_parse import parse_status_v2

# Spec 4.4 lists only HEAD, index and logs/HEAD. That set misses branch
# creation (writes refs/heads/<name>) and fetch (writes remote refs and
# packed-refs), so both are watched here too. The leaf ref directories are
# watched individually: creating refs/heads/x bumps refs/heads, not refs.
_WATCH_PATHS = (
    "HEAD",
    "index",
    "logs/HEAD",
    "refs",
    "refs/heads",
    "refs/remotes",
    "refs/tags",
    "refs/tutorial",
    "packed-refs",
    "MERGE_HEAD",
    "ORIG_HEAD",
    "rebase-merge",
    "rebase-apply",
)

_LOCK_FILES = ("index.lock", "packed-refs.lock", "shallow.lock")

# Some network and Windows filesystems report mtime at 1-2s resolution, so two
# changes inside one second with identical size are invisible. Periodically
# ignore the gate entirely.
FORCED_REFRESH_EVERY = 15

_REV_LIST_FORMAT = "%H%x1f%P%x1f%T%x1f%ct%x1f%s"


@dataclass(frozen=True, slots=True)
class Fingerprint:
    parts: tuple[tuple[str, int, int, int] | None, ...]
    forced: bool = False

    def changed_from(self, other: Fingerprint | None) -> bool:
        if other is None or self.forced:
            return True
        return self.parts != other.parts


class GitRepoProbe:
    """Reads a repository. Never writes to it."""

    def __init__(self, repo_path: Path, runner: GitRunner | None = None) -> None:
        self.location: RepoLocation = discover(Path(repo_path), runner)
        self.runner = runner or GitRunner(self.location.worktree)
        self._ticks = 0

    @property
    def git_dir(self) -> Path:
        return self.location.git_dir

    def locked(self) -> str | None:
        for name in _LOCK_FILES:
            if (self.git_dir / name).exists():
                return name
        return None

    def fingerprint(self) -> Fingerprint | None:
        """None means the repo is mid-write; the caller must skip this tick."""
        if self.locked() is not None:
            return None

        self._ticks += 1
        forced = self._ticks % FORCED_REFRESH_EVERY == 0

        parts: list[tuple[str, int, int, int] | None] = []
        # Each remote's own folder too: `fetch --prune` and `push --delete`
        # remove refs/remotes/origin/<name>, which changes that folder and
        # not refs/remotes above it.
        remotes = self.git_dir / "refs" / "remotes"
        try:
            leaves = sorted(f"refs/remotes/{d.name}" for d in remotes.iterdir() if d.is_dir())
        except OSError:
            leaves = []
        for name in (*_WATCH_PATHS, *leaves):
            try:
                st = (self.git_dir / name).stat()
            except (OSError, ValueError):
                parts.append(None)
            else:
                parts.append((name, st.st_mtime_ns, st.st_size, st.st_ino))
        return Fingerprint(parts=tuple(parts), forced=forced)

    def snapshot(self) -> RepoSnapshot:
        status = parse_status_v2(
            self.runner.run(
                "status", "--porcelain=v2", "--branch", "--untracked-files=all", "-z"
            ).stdout
        )

        refs = parse_for_each_ref(
            self.runner.run("for-each-ref", f"--format={REF_FORMAT}", *REF_NAMESPACES).stdout
        )

        # --reflog is load-bearing: Act 3 asserts over commits left unreachable
        # by `reset --hard`, which --all alone would omit entirely.
        graph = parse_rev_list(
            self.runner.run(
                "rev-list",
                "--all",
                "--reflog",
                "--single-worktree",
                "--no-commit-header",
                f"--format={_REV_LIST_FORMAT}",
            ).stdout
        )

        index_blobs = _parse_ls_files(self.runner.run("ls-files", "-s", "-z").stdout)

        dirty = sorted(
            {e.path for e in status.entries
             if (e.kind in ("ordinary", "renamed") and e.is_dirty) or e.kind == "unmerged"}
        )
        worktree_blobs = self._hash_worktree(dirty)

        return RepoSnapshot(
            head_ref=status.head_ref,
            head_sha=status.head_sha,
            branches=refs.branches,
            tags=refs.tags,
            tutorial_refs=refs.tutorial_refs,
            remote_refs=refs.remote_refs,
            special_refs=self._read_special_refs(),
            upstream=refs.upstream,
            ahead_behind=status.ahead_behind,
            status=status.entries,
            graph=graph,
            in_progress=self._read_in_progress(),
            stash_count=self._read_stash_count(),
            index_blobs=index_blobs,
            worktree_blobs=worktree_blobs,
            taken_at=time.time(),
        )

    def blobs(self) -> BlobReader:
        return BlobReader(self.runner)

    def events(self, *, since: Mapping[str, int] | None = None) -> tuple[GitEvent, ...]:
        """Every reflog's events, oldest first (spec 5.1).

        Read whole rather than tailed: a check wants the level's whole window
        and the logs are a few kilobytes. The offsets are what makes a window
        a window - see `reflog.since_offsets`.
        """
        events, _ = reflog.read_all(self.git_dir, since=since)
        return events

    def reflog_offsets(self) -> dict[str, int]:
        """Where the reflogs end now: the mark a level's window starts at."""
        return reflog.offsets(self.git_dir)

    def _hash_worktree(self, paths: list[str]) -> dict[str, str]:
        if not paths:
            return {}
        payload = "\n".join(paths).encode("utf-8", errors="surrogateescape") + b"\n"
        out = self.runner.run("hash-object", "--stdin-paths", stdin=payload).stdout
        return dict(zip(paths, out.split(), strict=False))

    def _read_special_refs(self) -> dict[str, str]:
        found: dict[str, str] = {}
        for name in SPECIAL_REF_FILES:
            try:
                text = (self.git_dir / name).read_text(encoding="utf-8").strip()
            except OSError:
                continue
            if text:
                found[name] = text.split()[0]
        return found

    def _read_in_progress(self) -> frozenset[str]:
        markers = {name for name in IN_PROGRESS_FILES if (self.git_dir / name).exists()}
        markers |= {name for name in IN_PROGRESS_DIRS if (self.git_dir / name).is_dir()}
        return frozenset(markers)

    def _read_stash_count(self) -> int:
        try:
            raw = (self.git_dir / "logs" / "refs" / "stash").read_bytes()
        except OSError:
            return 0
        return raw.count(b"\n")


def _parse_ls_files(payload: str) -> dict[str, str]:
    """Parses `ls-files -s -z`: `<mode> <sha> <stage>\\t<path>`. Stage 0 only."""
    blobs: dict[str, str] = {}
    for record in payload.split("\0"):
        if not record:
            continue
        meta, _, path = record.partition("\t")
        fields = meta.split()
        if len(fields) != 3 or fields[2] != "0":
            continue
        blobs[path] = fields[1]
    return blobs
