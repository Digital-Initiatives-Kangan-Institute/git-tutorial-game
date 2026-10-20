from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from git_tutorial.checker import CheckReport
from git_tutorial.state.models import AssertionSnapshot


class TransitionKind(StrEnum):
    ASSERTION_PASSED = "assertion_passed"
    ASSERTION_REGRESSED = "assertion_regressed"
    LEVEL_COMPLETE = "level_complete"


@dataclass(frozen=True, slots=True)
class Transition:
    kind: TransitionKind
    key: str
    detail: str = ""


def to_snapshots(report: CheckReport) -> list[AssertionSnapshot]:
    return [AssertionSnapshot(key=key, passed=passed) for key, passed in report.signature()]


def diff(previous: Sequence[AssertionSnapshot], report: CheckReport) -> tuple[Transition, ...]:
    was = {snap.key: snap.passed for snap in previous}
    out: list[Transition] = []

    for (key, passed), result in zip(report.signature(), report.results, strict=True):
        before = was.get(key)
        if before is None or before == passed:
            continue
        kind = (
            TransitionKind.ASSERTION_PASSED if passed else TransitionKind.ASSERTION_REGRESSED
        )
        out.append(Transition(kind=kind, key=key, detail=result.label or result.want))

    was_complete = bool(previous) and all(snap.passed for snap in previous)
    if report.complete and not was_complete:
        out.append(Transition(kind=TransitionKind.LEVEL_COMPLETE, key=report.level_id))

    return tuple(out)
