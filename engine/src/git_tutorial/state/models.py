from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

SCHEMA_VERSION = 1

RECAP_LIMIT = 20

# Serialisation is hand-written rather than dataclasses.asdict so that unknown
# keys written by a newer engine survive a round-trip through an older one.
_EXTRA = "_extra"


def _extras(raw: Mapping[str, Any], known: set[str]) -> dict[str, Any]:
    return {k: v for k, v in raw.items() if k not in known}


@dataclass(slots=True)
class AssertionSnapshot:
    key: str  # "0:branch_exists" — matches CheckReport.signature()
    passed: bool

    def to_dict(self) -> dict[str, Any]:
        return {"key": self.key, "passed": self.passed}

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> AssertionSnapshot:
        return cls(key=str(raw["key"]), passed=bool(raw["passed"]))


@dataclass(slots=True)
class RecapEntry:
    at: float
    text: str

    def to_dict(self) -> dict[str, Any]:
        return {"at": self.at, "text": self.text}

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> RecapEntry:
        return cls(at=float(raw.get("at", 0.0)), text=str(raw.get("text", "")))


@dataclass(slots=True)
class LevelProgress:
    level_id: str
    started_at: float = 0.0
    start_head: str = ""
    start_worktree: dict[str, str] = field(default_factory=dict)
    start_offsets: dict[str, int] = field(default_factory=dict)  # M3
    # Where the reflogs ended when this level was finished. The pair of
    # marks is what makes "what the player did on this level" exact: the
    # next level's setup runs before the next level's start mark exists,
    # so without this its commits are attributed to the level just passed.
    end_offsets: dict[str, int] = field(default_factory=dict)
    # What the player did on this level, counted from the reflog at the
    # moment they finished it. Recorded rather than derived later because
    # later levels delete branches - and a deleted branch takes its reflog
    # with it, so by the end of the course act 4's pushes are unreadable.
    deeds: dict[str, int] = field(default_factory=dict)
    completed_at: float | None = None
    hints_shown: list[int] = field(default_factory=list)
    hints_shown_at: list[float] = field(default_factory=list)
    solve_used: bool = False
    reset_count: int = 0
    attempt: int = 1
    answers: dict[str, str] = field(default_factory=dict)
    last_results: list[AssertionSnapshot] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def completed(self) -> bool:
        return self.completed_at is not None

    def to_dict(self) -> dict[str, Any]:
        return {
            "level_id": self.level_id,
            "started_at": self.started_at,
            "start_head": self.start_head,
            "start_worktree": dict(self.start_worktree),
            "start_offsets": dict(self.start_offsets),
            "end_offsets": dict(self.end_offsets),
            "deeds": dict(self.deeds),
            "completed_at": self.completed_at,
            "hints_shown": list(self.hints_shown),
            "hints_shown_at": list(self.hints_shown_at),
            "solve_used": self.solve_used,
            "reset_count": self.reset_count,
            "attempt": self.attempt,
            "answers": dict(self.answers),
            "last_results": [r.to_dict() for r in self.last_results],
            **self.extra,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> LevelProgress:
        known = {
            "level_id", "started_at", "start_head", "start_worktree", "start_offsets",
            "end_offsets", "deeds",
            "completed_at", "hints_shown", "hints_shown_at", "solve_used", "reset_count",
            "attempt", "answers", "last_results",
        }
        return cls(
            level_id=str(raw["level_id"]),
            started_at=float(raw.get("started_at", 0.0)),
            start_head=str(raw.get("start_head", "")),
            start_worktree=dict(raw.get("start_worktree") or {}),
            start_offsets=dict(raw.get("start_offsets") or {}),
            end_offsets=dict(raw.get("end_offsets") or {}),
            deeds={str(k): int(v) for k, v in (raw.get("deeds") or {}).items()},
            completed_at=raw.get("completed_at"),
            hints_shown=[int(i) for i in raw.get("hints_shown") or []],
            hints_shown_at=[float(f) for f in raw.get("hints_shown_at") or []],
            solve_used=bool(raw.get("solve_used", False)),
            reset_count=int(raw.get("reset_count", 0)),
            attempt=int(raw.get("attempt", 1)),
            answers=dict(raw.get("answers") or {}),
            last_results=[AssertionSnapshot.from_dict(r) for r in raw.get("last_results") or []],
            extra=_extras(raw, known),
        )


@dataclass(slots=True)
class Progress:
    schema_version: int = SCHEMA_VERSION
    repo_path: str = ""
    pack_id: str = ""
    pack_version: str = ""
    current_level_id: str | None = None
    completed: list[str] = field(default_factory=list)
    levels: dict[str, LevelProgress] = field(default_factory=dict)
    recap: list[RecapEntry] = field(default_factory=list)
    created_at: float = 0.0
    updated_at: float = 0.0
    finished_at: float | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def started(self) -> bool:
        return bool(self.current_level_id or self.completed)

    @property
    def finished(self) -> bool:
        return self.finished_at is not None

    def current(self) -> LevelProgress | None:
        if self.current_level_id is None:
            return None
        return self.levels.get(self.current_level_id)

    def for_level(self, level_id: str) -> LevelProgress:
        entry = self.levels.get(level_id)
        if entry is None:
            entry = LevelProgress(level_id=level_id)
            self.levels[level_id] = entry
        return entry

    def add_recap(self, at: float, text: str) -> None:
        self.recap.append(RecapEntry(at=at, text=text))
        del self.recap[:-RECAP_LIMIT]

    def recent_recap(self, limit: int = 3) -> tuple[str, ...]:
        return tuple(entry.text for entry in self.recap[-limit:])

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "repo_path": self.repo_path,
            "pack_id": self.pack_id,
            "pack_version": self.pack_version,
            "current_level_id": self.current_level_id,
            "completed": list(self.completed),
            "levels": {k: v.to_dict() for k, v in self.levels.items()},
            "recap": [r.to_dict() for r in self.recap],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "finished_at": self.finished_at,
            **self.extra,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> Progress:
        known = {
            "schema_version", "repo_path", "pack_id", "pack_version", "current_level_id",
            "completed", "levels", "recap", "created_at", "updated_at", "finished_at",
        }
        return cls(
            schema_version=int(raw.get("schema_version", SCHEMA_VERSION)),
            repo_path=str(raw.get("repo_path", "")),
            pack_id=str(raw.get("pack_id", "")),
            pack_version=str(raw.get("pack_version", "")),
            current_level_id=raw.get("current_level_id"),
            completed=[str(c) for c in raw.get("completed") or []],
            levels={
                str(k): LevelProgress.from_dict(v) for k, v in (raw.get("levels") or {}).items()
            },
            recap=[RecapEntry.from_dict(r) for r in raw.get("recap") or []],
            created_at=float(raw.get("created_at", 0.0)),
            updated_at=float(raw.get("updated_at", 0.0)),
            finished_at=raw.get("finished_at"),
            extra=_extras(raw, known),
        )


@dataclass(slots=True)
class LogCursor:
    """M3's shape, defined now so the file format does not change later."""

    path: str
    offset: int
    size: int
    mtime_ns: int
    head_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "offset": self.offset,
            "size": self.size,
            "mtime_ns": self.mtime_ns,
            "head_digest": self.head_digest,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> LogCursor:
        return cls(
            path=str(raw["path"]),
            offset=int(raw.get("offset", 0)),
            size=int(raw.get("size", 0)),
            mtime_ns=int(raw.get("mtime_ns", 0)),
            head_digest=str(raw.get("head_digest", "")),
        )


@dataclass(slots=True)
class CursorFile:
    schema_version: int = SCHEMA_VERSION
    cursors: dict[str, LogCursor] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "cursors": {k: v.to_dict() for k, v in self.cursors.items()},
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> CursorFile:
        return cls(
            schema_version=int(raw.get("schema_version", SCHEMA_VERSION)),
            cursors={
                str(k): LogCursor.from_dict(v) for k, v in (raw.get("cursors") or {}).items()
            },
        )
