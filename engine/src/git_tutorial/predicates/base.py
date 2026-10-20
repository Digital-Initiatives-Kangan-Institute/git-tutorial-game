from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from git_tutorial.errors import LevelAuthoringError
from git_tutorial.git.blobs import BlobReader
from git_tutorial.git.reflog import GitEvent
from git_tutorial.git.snapshot import RepoSnapshot


@dataclass(frozen=True, slots=True)
class AssertionResult:
    kind: str
    passed: bool
    want: str
    found: str
    detail: str | None = None
    # A level authoring error, not a student failure. Spec 6.2 requires these
    # be surfaced distinctly, so they get their own channel rather than being
    # flattened into passed=False.
    error: str | None = None
    # False under `technique: loose` for technique-gated predicates: still
    # evaluated and shown, but not blocking completion.
    enforced: bool = True
    label: str | None = None

    @property
    def blocking(self) -> bool:
        return self.error is not None or (self.enforced and not self.passed)


# Keys every assertion may carry that the predicate itself never reads: the
# job sheet's goal line, its warehouse flavour line, and an answer's input
# type. The browser reads them straight from the level.
PRESENTATION = ("label", "story", "input")


@dataclass(frozen=True, slots=True)
class ArgsSpec:
    """Declares a predicate's arguments so level YAML is validated at load time."""

    required: tuple[str, ...] = ()
    optional: tuple[str, ...] = ()
    one_of: tuple[tuple[str, ...], ...] = ()
    # (arg, allowed values). For args whose value is drawn from a fixed
    # vocabulary: a typo there is otherwise a level that silently passes.
    # A list-valued arg is checked element by element, and an empty one is
    # rejected: `ops: []` makes `used_command` unpassable and
    # `not_used_command` true in every repository on earth.
    choices: tuple[tuple[str, tuple[str, ...]], ...] = ()

    def validate(self, kind: str, args: Mapping[str, Any]) -> None:
        keys = set(args)
        missing = [name for name in self.required if name not in keys]
        if missing:
            raise LevelAuthoringError(f"{kind}: missing required arg(s): {', '.join(missing)}")

        allowed = (
            set(self.required) | set(self.optional) | {n for g in self.one_of for n in g}
            | set(PRESENTATION)
        )
        unknown = sorted(keys - allowed)
        if unknown:
            raise LevelAuthoringError(
                f"{kind}: unknown arg(s): {', '.join(unknown)}. "
                f"Accepted: {', '.join(sorted(allowed)) or '(none)'}"
            )

        for name, allowed_values in self.choices:
            if name not in keys:
                continue
            value = args[name]
            listed = isinstance(value, (list, tuple))
            if listed and not value:
                raise LevelAuthoringError(
                    f"{kind}: {name} is empty, so the assertion could never "
                    f"say anything. Name at least one of: {', '.join(allowed_values)}"
                )
            for item in value if listed else [value]:
                if str(item) not in allowed_values:
                    raise LevelAuthoringError(
                        f"{kind}: {name}={item!r} is not one of "
                        f"{', '.join(allowed_values)}"
                    )

        for group in self.one_of:
            present = [name for name in group if name in keys]
            if len(present) != 1:
                raise LevelAuthoringError(
                    f"{kind}: exactly one of {', '.join(group)} is required, got "
                    + (", ".join(present) if present else "none")
                )


@dataclass(frozen=True)
class EvalContext:
    """Everything a predicate is allowed to see.

    Replaces the spec 6.1 signature, which could not reach @start, the
    technique setting, or blob content.
    """

    snapshot: RepoSnapshot
    events: Sequence[GitEvent] = ()
    blobs: BlobReader | None = None
    level_start_sha: str | None = None
    level_start_offsets: Mapping[str, int] = field(default_factory=dict)
    level_start_worktree: Mapping[str, str] = field(default_factory=dict)
    technique: str = "loose"
    answers: Mapping[str, str] = field(default_factory=dict)


Predicate = Callable[[EvalContext, Mapping[str, Any]], AssertionResult]


@dataclass(frozen=True, slots=True)
class Registration:
    kind: str
    fn: Predicate
    args: ArgsSpec
    technique_gated: bool


REGISTRY: dict[str, Registration] = {}


def register(
    kind: str, *, args: ArgsSpec, technique_gated: bool = False
) -> Callable[[Predicate], Predicate]:
    def decorate(fn: Predicate) -> Predicate:
        if kind in REGISTRY:
            raise RuntimeError(f"predicate {kind!r} is already registered")
        REGISTRY[kind] = Registration(kind=kind, fn=fn, args=args, technique_gated=technique_gated)
        return fn

    return decorate


def get(kind: str) -> Registration:
    try:
        return REGISTRY[kind]
    except KeyError:
        raise LevelAuthoringError(
            f"unknown assertion kind {kind!r}. Known kinds: {', '.join(sorted(REGISTRY))}"
        ) from None


def evaluate(kind: str, ctx: EvalContext, args: Mapping[str, Any]) -> AssertionResult:
    """Runs one predicate, converting any authoring error into a result row."""
    from git_tutorial.errors import TutorialError
    from git_tutorial.predicates.resolve import RefNotYetPresent

    try:
        registration = get(kind)
        registration.args.validate(kind, args)
        result = registration.fn(ctx, args)
    except RefNotYetPresent as exc:
        # Ordinary unfinished work, not a broken level.
        return AssertionResult(
            kind=kind,
            passed=False,
            want=str(args.get("label") or f"{kind} holds"),
            found=str(exc),
        )
    except TutorialError as exc:
        return AssertionResult(
            kind=kind, passed=False, want="(could not evaluate)", found="", error=str(exc)
        )

    if registration.technique_gated and ctx.technique != "strict":
        result = AssertionResult(**{**_as_dict(result), "enforced": False})
    if args.get("label"):
        result = AssertionResult(**{**_as_dict(result), "label": str(args["label"])})
    return result


def _as_dict(result: AssertionResult) -> dict[str, Any]:
    return {
        "kind": result.kind,
        "passed": result.passed,
        "want": result.want,
        "found": result.found,
        "detail": result.detail,
        "error": result.error,
        "enforced": result.enforced,
        "label": result.label,
    }
