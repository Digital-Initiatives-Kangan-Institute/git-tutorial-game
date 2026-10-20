from __future__ import annotations

import re
from collections.abc import Mapping
from itertools import pairwise
from pathlib import Path
from typing import Any

import yaml

from git_tutorial.errors import LevelAuthoringError
from git_tutorial.levels.model import (
    AssertionSpec,
    BeatSpec,
    HintSpec,
    JobSpec,
    Level,
    ProseSpec,
)
from git_tutorial.predicates import base as predicates

_DURATION = re.compile(r"^(\d+)(s|m|h)?$")
_UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600}


def parse_duration(value: object) -> int:
    if isinstance(value, int):
        return value
    match = _DURATION.match(str(value).strip())
    if match is None:
        raise LevelAuthoringError(f"could not read duration {value!r} (try `180s` or `5m`)")
    return int(match.group(1)) * _UNIT_SECONDS[match.group(2) or "s"]


def _require(data: Mapping[str, Any], key: str, path: Path) -> Any:
    if key not in data:
        raise LevelAuthoringError(f"{path}: missing required field {key!r}")
    return data[key]


def _assertion(spec: Any, path: Path) -> AssertionSpec:
    if not isinstance(spec, Mapping) or "kind" not in spec:
        raise LevelAuthoringError(f"{path}: each assertion needs a `kind`")
    kind = str(spec["kind"])
    args = {k: v for k, v in spec.items() if k != "kind"}
    # Validate now, so an authoring typo fails in content CI rather than
    # halfway through a student's session.
    predicates.get(kind).args.validate(kind, args)
    return AssertionSpec(kind=kind, args=args)


def load_level(path: Path) -> Level:
    """Loads one level.yaml. Raises LevelAuthoringError on anything malformed."""
    path = Path(path)
    directory = path.parent
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise LevelAuthoringError(f"{path}: could not read level definition: {exc}") from exc

    if not isinstance(data, Mapping):
        raise LevelAuthoringError(f"{path}: level definition must be a mapping")

    technique = str(data.get("technique", "loose"))
    if technique not in ("loose", "strict"):
        raise LevelAuthoringError(f"{path}: technique must be `loose` or `strict`")

    prose_raw = data.get("prose") or {}
    beats = tuple(
        BeatSpec(
            on_state=_assertion(beat["on_state"], path),
            text=str(beat["text"]),
            once=bool(beat.get("once", True)),
        )
        for beat in prose_raw.get("beats", [])
    )

    hints = tuple(
        HintSpec(after_idle=parse_duration(hint["after_idle"]), text=str(hint["text"]))
        for hint in data.get("hints", [])
    )
    for earlier, later in pairwise(hints):
        if later.after_idle <= earlier.after_idle:
            raise LevelAuthoringError(f"{path}: hint after_idle values must increase")

    return Level(
        id=str(_require(data, "id", path)),
        act=int(_require(data, "act", path)),
        level=int(data.get("level", 0)),
        title=str(_require(data, "title", path)),
        directory=directory,
        teaches=tuple(str(t) for t in data.get("teaches", [])),
        reuses=tuple(str(t) for t in data.get("reuses", [])),
        requires=tuple(str(t) for t in data.get("requires", [])),
        technique=technique,  # type: ignore[arg-type]
        first_month_moment=str(data.get("first_month_moment", "")),
        estimated_minutes=int(data.get("estimated_minutes", 15)),
        budget_exception=(
            str(data["budget_exception"]) if data.get("budget_exception") else None
        ),
        setup=str(data["setup"]) if data.get("setup") else None,
        solution=str(data["solution"]) if data.get("solution") else None,
        prose=ProseSpec(
            intro=prose_raw.get("intro"),
            brief=prose_raw.get("brief"),
            success=prose_raw.get("success"),
            beats=beats,
        ),
        assertions=tuple(_assertion(a, path) for a in data.get("assert", [])),
        hints=hints,
        job=_job(data.get("job"), path),
        draft=bool(data.get("draft", False)),
    )


def _job(raw: Any, path: Path) -> JobSpec | None:
    if raw is None:
        return None
    if not isinstance(raw, Mapping) or not {"ticket", "from", "title"} <= set(raw):
        raise LevelAuthoringError(f"{path}: `job` needs ticket, from and title")
    return JobSpec(ticket=str(raw["ticket"]), sender=str(raw["from"]), title=str(raw["title"]))
