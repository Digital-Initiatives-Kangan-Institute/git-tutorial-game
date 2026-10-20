from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

StatusKind = Literal["ordinary", "renamed", "unmerged", "untracked", "ignored"]


@dataclass(frozen=True, slots=True)
class StatusEntry:
    path: str
    kind: StatusKind
    index_status: str = "."
    worktree_status: str = "."
    orig_path: str | None = None
    unmerged_stages: tuple[str, ...] = ()

    @property
    def is_staged(self) -> bool:
        return self.index_status not in (".", "?", "!")

    @property
    def is_dirty(self) -> bool:
        return self.worktree_status not in (".", "?", "!")


@dataclass(frozen=True, slots=True)
class StatusReport:
    head_ref: str | None  # None when detached
    head_sha: str
    upstream: str | None
    ahead_behind: tuple[int, int] | None
    entries: tuple[StatusEntry, ...] = field(default=())


_DETACHED = "(detached)"
_UNBORN = "(initial)"
_NULL_SHA = "0" * 40


def parse_status_v2(payload: str) -> StatusReport:
    """Parses `status --porcelain=v2 --branch --untracked-files=all -z`.

    With -z each record is NUL-terminated. A rename record (type 2) is followed
    by its original path as a separate NUL-terminated field, so records cannot
    be split on NUL alone without tracking that lookahead.
    """
    records = [r for r in payload.split("\0") if r != ""]

    head_ref: str | None = None
    head_sha = _NULL_SHA
    upstream: str | None = None
    ahead_behind: tuple[int, int] | None = None
    entries: list[StatusEntry] = []

    index = 0
    while index < len(records):
        record = records[index]
        index += 1

        if record.startswith("# "):
            key, _, value = record[2:].partition(" ")
            if key == "branch.oid":
                head_sha = _NULL_SHA if value == _UNBORN else value
            elif key == "branch.head":
                head_ref = None if value == _DETACHED else value
            elif key == "branch.upstream":
                upstream = value
            elif key == "branch.ab":
                ahead_behind = _parse_ab(value)
            continue

        code, _, rest = record.partition(" ")

        if code == "?":
            entries.append(StatusEntry(path=rest, kind="untracked", index_status="?",
                                       worktree_status="?"))
        elif code == "!":
            entries.append(StatusEntry(path=rest, kind="ignored", index_status="!",
                                       worktree_status="!"))
        elif code == "1":
            fields = rest.split(" ", 7)
            xy = fields[0]
            entries.append(
                StatusEntry(
                    path=fields[7],
                    kind="ordinary",
                    index_status=xy[0],
                    worktree_status=xy[1],
                )
            )
        elif code == "2":
            fields = rest.split(" ", 8)
            xy = fields[0]
            orig = records[index] if index < len(records) else None
            index += 1
            entries.append(
                StatusEntry(
                    path=fields[8],
                    kind="renamed",
                    index_status=xy[0],
                    worktree_status=xy[1],
                    orig_path=orig,
                )
            )
        elif code == "u":
            # u <XY> <sub> <m1> <m2> <m3> <mW> <h1> <h2> <h3> <path>
            fields = rest.split(" ", 9)
            xy = fields[0]
            entries.append(
                StatusEntry(
                    path=fields[9],
                    kind="unmerged",
                    index_status=xy[0],
                    worktree_status=xy[1],
                    unmerged_stages=tuple(fields[6:9]),
                )
            )

    return StatusReport(
        head_ref=head_ref,
        head_sha=head_sha,
        upstream=upstream,
        ahead_behind=ahead_behind,
        entries=tuple(entries),
    )


def _parse_ab(value: str) -> tuple[int, int] | None:
    ahead_raw, _, behind_raw = value.partition(" ")
    try:
        return (int(ahead_raw.lstrip("+")), abs(int(behind_raw)))
    except ValueError:
        return None
