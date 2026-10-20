from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from git_tutorial.errors import LevelAuthoringError
from git_tutorial.predicates import base
from git_tutorial.predicates.base import ArgsSpec, AssertionResult, EvalContext, register


def _children(ctx: EvalContext, args: Mapping[str, Any]) -> list[AssertionResult]:
    specs = args["assert"]
    if not isinstance(specs, Sequence) or isinstance(specs, str):
        raise LevelAuthoringError("assert: must be a list of assertions")
    results: list[AssertionResult] = []
    for spec in specs:
        if not isinstance(spec, Mapping) or "kind" not in spec:
            raise LevelAuthoringError("each nested assertion needs a `kind`")
        inner = {k: v for k, v in spec.items() if k != "kind"}
        results.append(base.evaluate(str(spec["kind"]), ctx, inner))
    return results


def _summarise(results: list[AssertionResult], *, passed: bool) -> str:
    """What to show in the `found:` column for a composite.

    Two rules, both learned from reading the table as a student. Predicate
    kinds are internal names and never belong on screen. And `found` is
    written to explain a failure, so on a row that passed, only the children
    that passed have anything true to say — a `not` that holds is the case
    where none did, and there the children's words are right after all.
    """
    chosen = [r for r in results if r.passed == passed] or results

    seen: list[str] = []
    for result in chosen:
        if result.found and result.found not in seen:
            seen.append(result.found)
    return "; ".join(seen) if seen else "nothing to report"


@register("all_of", args=ArgsSpec(required=("assert",), optional=("label",)))
def all_of(ctx: EvalContext, args: Mapping[str, Any]) -> AssertionResult:
    results = _children(ctx, args)
    passed = all(r.passed for r in results)
    return AssertionResult(
        kind="all_of",
        passed=passed,
        want=f"all {len(results)} of: " + ", ".join(r.want for r in results),
        found=_summarise(results, passed=passed),
    )


@register("any_of", args=ArgsSpec(required=("assert",), optional=("label",)))
def any_of(ctx: EvalContext, args: Mapping[str, Any]) -> AssertionResult:
    results = _children(ctx, args)
    passed = any(r.passed for r in results)
    return AssertionResult(
        kind="any_of",
        passed=passed,
        want="any of: " + ", ".join(r.want for r in results),
        found=_summarise(results, passed=passed),
    )


@register("not", args=ArgsSpec(required=("assert",), optional=("label",)))
def not_(ctx: EvalContext, args: Mapping[str, Any]) -> AssertionResult:
    results = _children(ctx, args)
    passed = not any(r.passed for r in results)
    return AssertionResult(
        kind="not",
        passed=passed,
        want="none of: " + ", ".join(r.want for r in results),
        # Inverted: `not` holds precisely when no child did, so the children
        # worth quoting are the ones whose own verdict is the opposite.
        found=_summarise(results, passed=not passed),
    )
