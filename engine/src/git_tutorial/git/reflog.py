"""The reflog, read as an event stream (spec 5.1).

`.git/logs/HEAD` is a command log written by git itself - no hooks, no
wrapper, nothing the student has to opt into. It is what lifts the
end-state-only constraint: `reset` and `revert` can leave the same tree,
and only this file says which one was typed.

It is append-only, so a tick reads the tail from a stored byte offset
rather than the whole file. Append-only is not the same as immutable,
though: `wt reset` re-runs a level's setup, which rewrites history and
can leave the log shorter than the offset we recorded. Every read checks
for that and starts again from the beginning rather than returning the
middle of a line.
"""

from __future__ import annotations

import re
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

# <old> <new> <name> <email> <unix ts> <tz>\t<message>
_LINE = re.compile(
    r"^(?P<old>[0-9a-f]+) (?P<new>[0-9a-f]+) (?P<who>.*?) "
    r"(?P<at>\d+) (?P<tz>[+-]\d{4})\t(?P<message>.*)$"
)

# A message prefix that is one word, optionally qualified in brackets:
# `commit`, `commit (amend)`, `rebase (finish)`. Anything else before the
# colon carries an argument - `merge feature`, `pull origin main` - and the
# operation is its first word.
_OP = re.compile(r"^(?P<op>[a-z][a-z-]*(?: \([a-z ]+\))?)$")

# Spec 5.1. A level naming an op outside this set is an authoring error,
# because the assertion could never fire.
OPS = (
    "commit",
    "commit (amend)",
    "commit (initial)",
    "checkout",
    "reset",
    "merge",
    "pull",
    "clone",
    "rebase",
    "rebase (start)",
    "rebase (pick)",
    "rebase (finish)",
    "cherry-pick",
    "revert",
    "branch",
)


@dataclass(frozen=True, slots=True)
class GitEvent:
    """One line of one reflog."""

    ref: str  # "HEAD", or "refs/heads/<name>"
    op: str  # "reset", "commit (amend)", ... - see OPS
    old_sha: str
    new_sha: str
    at: int  # unix seconds, as git recorded them
    detail: str  # the message after the operation
    offset: int  # byte offset of this line's first byte

    @property
    def moved(self) -> bool:
        return self.old_sha != self.new_sha


def parse_line(line: str, *, ref: str, offset: int) -> GitEvent | None:
    """None for a line this does not understand, which is never fatal.

    A reflog we cannot parse must degrade to "no evidence", never to a
    traceback in front of a student who is already stuck.
    """
    match = _LINE.match(line)
    if match is None:
        return None

    head, _, detail = match.group("message").partition(": ")
    op = head if _OP.match(head) else head.split(" ", 1)[0]

    return GitEvent(
        ref=ref,
        op=op,
        old_sha=match.group("old"),
        new_sha=match.group("new"),
        at=int(match.group("at")),
        detail=detail,
        offset=offset,
    )


def read_log(path: Path, *, ref: str, since: int = 0) -> tuple[tuple[GitEvent, ...], int]:
    """Events from `since` onwards, and the offset to resume from next time.

    Only whole lines are consumed. A tick can land midway through git's own
    append, and half a line parsed now would be a line missed forever once
    the offset moved past it.
    """
    try:
        raw = path.read_bytes()
    except OSError:
        return (), 0

    # Shorter than the offset means the file was rewritten under us, not
    # appended to - a level setup rebuilding the repository, or `wt reset`.
    start = since if 0 <= since <= len(raw) else 0
    consumed = raw.rfind(b"\n", start)
    if consumed == -1:
        return (), start
    body = raw[start : consumed + 1].decode("utf-8", errors="replace")

    events: list[GitEvent] = []
    offset = start
    for line in body.splitlines(keepends=True):
        event = parse_line(line.rstrip("\n"), ref=ref, offset=offset)
        if event is not None:
            events.append(event)
        offset += len(line.encode("utf-8", errors="replace"))
    return tuple(events), consumed + 1


def log_paths(git_dir: Path) -> Iterator[tuple[str, Path]]:
    """Every reflog in the repository, as (ref name, path).

    HEAD first, then branches, then remote-tracking branches. The last of
    those is not an afterthought: it is where fetching and pushing are
    recorded, and 4.10 asks a student to read it to recover a commit they
    force-pushed over. A reader that skipped it would make the engine
    blind to the whole of act 4.

    The directories nest, so a branch called `fix/thing` is found by
    walking rather than listing.
    """
    head = git_dir / "logs" / "HEAD"
    if head.is_file():
        yield "HEAD", head

    for prefix in ("heads", "remotes"):
        root = git_dir / "logs" / "refs" / prefix
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if path.is_file():
                yield f"refs/{prefix}/{path.relative_to(root).as_posix()}", path


def read_all(
    git_dir: Path, *, since: Mapping[str, int] | None = None
) -> tuple[tuple[GitEvent, ...], dict[str, int]]:
    """Every reflog's tail, oldest event first, with the resume offsets.

    A ref with no recorded offset is read in full: a branch created during
    the level did not exist to have one, and all of its events belong to
    the window.
    """
    since = since or {}
    events: list[GitEvent] = []
    offsets: dict[str, int] = {}
    for ref, path in log_paths(git_dir):
        found, offsets[ref] = read_log(path, ref=ref, since=since.get(ref, 0))
        events.extend(found)
    events.sort(key=lambda e: (e.at, e.ref != "HEAD", e.offset))
    return tuple(events), offsets


def offsets(git_dir: Path) -> dict[str, int]:
    """Where every reflog currently ends - the mark a level starts from."""
    marks: dict[str, int] = {}
    for ref, path in log_paths(git_dir):
        try:
            marks[ref] = path.stat().st_size
        except OSError:
            marks[ref] = 0
    return marks


def last_activity(events: tuple[GitEvent, ...]) -> int | None:
    """When the student last did anything, by git's clock.

    Hint gating is on reflog silence, not wall-clock time (spec 7.1): a
    student reading `git log` for four minutes is working, and a student who
    has issued no commands for four minutes is stuck. Only this tells them
    apart.
    """
    return max((event.at for event in events), default=None)


def since_offsets(
    events: tuple[GitEvent, ...], offsets: Mapping[str, int]
) -> tuple[GitEvent, ...]:
    """The events a level's window contains.

    A ref with no recorded offset was created during the level, so every
    event on it is inside the window - which is the whole point of recording
    the marks after setup rather than counting lines.
    """
    return tuple(event for event in events if event.offset >= offsets.get(event.ref, 0))


# Operations that never write to HEAD's log, so they are counted from the
# ref whose log does record them.
BY_REF = ("branch", "fetch", "update")


def count_ops(events: Sequence[GitEvent]) -> dict[str, int]:
    """How many times each operation happened, counted once each.

    A commit writes a line to `logs/HEAD` and to the branch's own log, so
    counting every log would double it. Branch creation, fetching and
    pushing are the other way round: they write a ref's log and never
    HEAD's.
    """
    counts: dict[str, int] = {}
    for event in events:
        head = event.ref == "HEAD"
        if (not head) if event.op in BY_REF else head:
            counts[event.op] = counts.get(event.op, 0) + 1
    return counts
