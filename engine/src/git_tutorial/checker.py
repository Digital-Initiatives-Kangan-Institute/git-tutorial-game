from __future__ import annotations

from dataclasses import dataclass

from git_tutorial.levels.model import Level
from git_tutorial.predicates import base as predicates
from git_tutorial.predicates.base import AssertionResult, EvalContext


@dataclass(frozen=True, slots=True)
class CheckReport:
    level_id: str
    title: str
    results: tuple[AssertionResult, ...]

    @property
    def complete(self) -> bool:
        """Complete when nothing blocking remains.

        Advisory rows — technique-gated predicates under `technique: loose` —
        are shown but do not hold the level open.
        """
        return bool(self.results) and not any(r.blocking for r in self.results)

    @property
    def has_authoring_error(self) -> bool:
        return any(r.error is not None for r in self.results)

    def signature(self) -> tuple[tuple[str, bool], ...]:
        """Stable per-assertion pass state, for transition detection."""
        return tuple(
            (f"{i}:{r.kind}", r.passed) for i, r in enumerate(self.results)
        )


class Checker:
    @staticmethod
    def evaluate(level: Level, ctx: EvalContext) -> CheckReport:
        ctx_for_level = (
            ctx if ctx.technique == level.technique else _with_technique(ctx, level.technique)
        )
        results = tuple(
            predicates.evaluate(spec.kind, ctx_for_level, spec.args) for spec in level.assertions
        )
        return CheckReport(level_id=level.id, title=level.title, results=results)


def _with_technique(ctx: EvalContext, technique: str) -> EvalContext:
    return EvalContext(
        snapshot=ctx.snapshot,
        events=ctx.events,
        blobs=ctx.blobs,
        level_start_sha=ctx.level_start_sha,
        level_start_offsets=ctx.level_start_offsets,
        level_start_worktree=ctx.level_start_worktree,
        technique=technique,
        answers=ctx.answers,
    )
