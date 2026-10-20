from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class AnswerSlot:
    """One question the player can answer, as declared by a level."""

    id: str
    prompt: str
    level_id: str
    input: str = "text"  # "text", or "sha" for a commit id


@dataclass(frozen=True, slots=True)
class AnswersDocument:
    values: Mapping[str, str] = field(default_factory=dict)
    by_level: Mapping[str, Mapping[str, str]] = field(default_factory=dict)
    notices: tuple[str, ...] = ()
    section_level_ids: tuple[str, ...] = ()

    def for_level(self, level_id: str) -> Mapping[str, str]:
        return self.by_level.get(level_id, {})


def slots_for(level: object) -> tuple[AnswerSlot, ...]:
    """Every `answer` assertion a level declares, in order."""
    found: list[AnswerSlot] = []
    for spec in getattr(level, "assertions", ()):
        if spec.kind != "answer":
            continue
        key = str(spec.args.get("id", ""))
        if not key:
            continue
        found.append(
            AnswerSlot(
                id=key,
                prompt=str(spec.args.get("prompt", key)),
                level_id=str(getattr(level, "id", "")),
                input=(
                    "sha" if "equals_commit" in spec.args else str(spec.args.get("input", "text"))
                ),
            )
        )
    return tuple(found)
