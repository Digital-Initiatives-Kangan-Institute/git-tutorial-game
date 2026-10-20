from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

Technique = Literal["loose", "strict"]


@dataclass(frozen=True, slots=True)
class AssertionSpec:
    kind: str
    args: Mapping[str, Any] = field(default_factory=dict)

    @property
    def key(self) -> str:
        return self.kind


@dataclass(frozen=True, slots=True)
class HintSpec:
    after_idle: int  # seconds
    text: str


@dataclass(frozen=True, slots=True)
class BeatSpec:
    on_state: AssertionSpec
    text: str
    once: bool = True


@dataclass(frozen=True, slots=True)
class ProseSpec:
    intro: str | None = None
    brief: str | None = None
    success: str | None = None
    beats: tuple[BeatSpec, ...] = ()


@dataclass(frozen=True, slots=True)
class JobSpec:
    """The job ticket a level arrives as: the story's framing, never a goal."""

    ticket: str
    sender: str
    title: str


@dataclass(frozen=True, slots=True)
class Level:
    id: str
    act: int
    level: int
    title: str
    directory: Path
    teaches: tuple[str, ...] = ()
    reuses: tuple[str, ...] = ()
    requires: tuple[str, ...] = ()
    technique: Technique = "loose"
    first_month_moment: str = ""
    estimated_minutes: int = 15
    budget_exception: str | None = None
    setup: str | None = None
    solution: str | None = None
    prose: ProseSpec = field(default_factory=ProseSpec)
    assertions: tuple[AssertionSpec, ...] = ()
    hints: tuple[HintSpec, ...] = ()
    job: JobSpec | None = None
    # A level whose teaches/reuses are settled but whose content is not yet
    # written. The curriculum checks count it; the game never serves it.
    draft: bool = False

    @property
    def label(self) -> str:
        return f"act {self.act} · level {self.level}"

    def assertion_keys(self) -> Sequence[str]:
        """Stable identifiers for transition detection."""
        return [f"{i}:{spec.kind}" for i, spec in enumerate(self.assertions)]
