from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from git_tutorial.errors import LevelAuthoringError
from git_tutorial.git import reflog
from git_tutorial.git.reflog import GitEvent
from git_tutorial.predicates.base import ArgsSpec, AssertionResult, EvalContext, register
from git_tutorial.predicates.resolve import INDEX, WORKTREE, resolve

# Every predicate populates want and found even on success: `wt check` is a
# diagnostician, not a grader, and pass/fail alone teaches nothing (spec 6.3).


def _short(sha: str) -> str:
    return sha[:7]


@register("head_on_branch", args=ArgsSpec(required=("name",), optional=("label",)))
def head_on_branch(ctx: EvalContext, args: Mapping[str, Any]) -> AssertionResult:
    name = str(args["name"])
    actual = ctx.snapshot.head_ref
    found = f"on {actual}" if actual else "detached HEAD"
    return AssertionResult(
        kind="head_on_branch",
        passed=actual == name,
        want=f"HEAD attached to {name}",
        found=found,
    )


@register("head_detached", args=ArgsSpec(optional=("at", "label")))
def head_detached(ctx: EvalContext, args: Mapping[str, Any]) -> AssertionResult:
    snap = ctx.snapshot
    if not snap.detached:
        return AssertionResult(
            kind="head_detached",
            passed=False,
            want="HEAD detached",
            found=f"attached to {snap.head_ref}",
        )
    if "at" not in args:
        return AssertionResult(
            kind="head_detached",
            passed=True,
            want="HEAD detached",
            found=f"detached at {_short(snap.head_sha)}",
        )
    target = resolve(ctx, str(args["at"]))
    return AssertionResult(
        kind="head_detached",
        passed=snap.head_sha == target,
        want=f"HEAD detached at {args['at']} ({_short(target)})",
        found=f"detached at {_short(snap.head_sha)}",
    )


@register("branch_exists", args=ArgsSpec(required=("name",), optional=("exists", "label")))
def branch_exists(ctx: EvalContext, args: Mapping[str, Any]) -> AssertionResult:
    name = str(args["name"])
    want_exists = bool(args.get("exists", True))
    sha = ctx.snapshot.branches.get(name)
    return AssertionResult(
        kind="branch_exists",
        passed=(sha is not None) == want_exists,
        want=f"branch {name} {'exists' if want_exists else 'is gone'}",
        found=f"{name} at {_short(sha)}" if sha else f"no branch {name}",
    )


@register("branch_at", args=ArgsSpec(required=("name", "commit"), optional=("label",)))
def branch_at(ctx: EvalContext, args: Mapping[str, Any]) -> AssertionResult:
    name = str(args["name"])
    target = resolve(ctx, str(args["commit"]))
    sha = ctx.snapshot.branches.get(name)
    return AssertionResult(
        kind="branch_at",
        passed=sha == target,
        want=f"{name} at {args['commit']} ({_short(target)})",
        found=f"{name} at {_short(sha)}" if sha else f"no branch {name}",
    )


@register("is_ancestor", args=ArgsSpec(required=("ancestor", "descendant"), optional=("label",)))
def is_ancestor(ctx: EvalContext, args: Mapping[str, Any]) -> AssertionResult:
    ancestor = resolve(ctx, str(args["ancestor"]))
    descendant = resolve(ctx, str(args["descendant"]))
    holds = ctx.snapshot.graph.is_ancestor(ancestor, descendant)
    return AssertionResult(
        kind="is_ancestor",
        passed=holds,
        want=f"{args['ancestor']} is reachable from {args['descendant']}",
        found="reachable" if holds else f"{_short(ancestor)} is not in that history",
    )


@register(
    "commit_reachable",
    args=ArgsSpec(
        required=("from",),
        optional=("label", "not_from"),
        one_of=(("message_matches", "contains_file", "file_matches"),),
    ),
)
def commit_reachable(ctx: EvalContext, args: Mapping[str, Any]) -> AssertionResult:
    start = resolve(ctx, str(args["from"]))
    graph = ctx.snapshot.graph

    # Without not_from, "the commit you just made" is satisfied by any commit
    # that shipped in the practice history bundle.
    excluded: set[str] = set()
    if "not_from" in args:
        excluded = set(graph.ancestors(resolve(ctx, str(args["not_from"]))))

    def candidates() -> list[str]:
        return [sha for sha in graph.ancestors(start) if sha not in excluded]

    if "message_matches" in args:
        subject_pattern = re.compile(str(args["message_matches"]))
        criterion = f"a commit whose message matches /{subject_pattern.pattern}/"
        for sha in candidates():
            node = graph.get(sha)
            if node and subject_pattern.search(node.subject):
                return AssertionResult(
                    kind="commit_reachable",
                    passed=True,
                    want=criterion,
                    found=f"{_short(sha)} {node.subject}",
                )
        return AssertionResult(
            kind="commit_reachable", passed=False, want=criterion,
            found="no commit says that",
        )

    if "contains_file" in args:
        path = str(args["contains_file"])
        pattern: re.Pattern[str] | None = None
        criterion = f"a commit containing {path}"
    else:
        # file_matches needs both a path and a pattern, so it takes a mapping:
        #   file_matches: {path: chronicle/ledger.md, matches: "the seal"}
        spec = args["file_matches"]
        if not isinstance(spec, Mapping) or "path" not in spec or "matches" not in spec:
            raise LevelAuthoringError(
                "file_matches must be a mapping with `path` and `matches`"
            )
        path = str(spec["path"])
        pattern = re.compile(str(spec["matches"]))
        criterion = f"a commit where {path} matches /{pattern.pattern}/"

    if ctx.blobs is None:
        raise LevelAuthoringError("commit_reachable with a file filter needs blob access")

    for sha in candidates():
        content = ctx.blobs.read_text(f"{sha}:{path}")
        if content is None:
            continue
        if pattern is None or pattern.search(content):
            return AssertionResult(
                kind="commit_reachable", passed=True, want=criterion, found=f"in {_short(sha)}"
            )
    return AssertionResult(
        kind="commit_reachable", passed=False, want=criterion, found="no commit has it"
    )


@register("parent_count", args=ArgsSpec(required=("of", "count"), optional=("label",)))
def parent_count(ctx: EvalContext, args: Mapping[str, Any]) -> AssertionResult:
    sha = resolve(ctx, str(args["of"]))
    expected = int(args["count"])
    node = ctx.snapshot.graph.require(sha)
    actual = len(node.parents)
    # Read on its own next to a glyph, so these name the commit rather than
    # describing a graph: "a linear commit" is reviewer shorthand.
    shape = {0: "the first commit", 1: "an ordinary commit", 2: "a merge commit"}
    return AssertionResult(
        kind="parent_count",
        passed=actual == expected,
        want=f"{args['of']} is {shape.get(expected, 'an octopus merge')} "
             f"({expected} parent(s))",
        found=f"{shape.get(actual, 'an octopus merge')} ({actual} parent(s))",
    )


@register(
    "file_content",
    args=ArgsSpec(
        required=("path",),
        optional=("at", "label"),
        one_of=(("equals", "contains", "matches"),),
    ),
)
def file_content(ctx: EvalContext, args: Mapping[str, Any]) -> AssertionResult:
    path = str(args["path"])
    at = str(args.get("at", WORKTREE))
    content = _read_at(ctx, at, path)

    # `found` is read on passing rows too, so it describes the file rather
    # than announcing a verdict. A byte count and "condition does not hold"
    # tell a student nothing and read as an error on a row that passed.
    if "equals" in args:
        expected = str(args["equals"])
        want = f"{path} at {at} equals the expected text"
        passed = content == expected
        found = "exactly that text" if passed else "different text"
    elif "contains" in args:
        needle = str(args["contains"])
        want = f"{path} at {at} contains {needle!r}"
        passed = content is not None and needle in content
        found = f"contains {needle!r}" if passed else f"no {needle!r} in it"
    else:
        pattern = re.compile(str(args["matches"]))
        want = f"{path} at {at} matches /{pattern.pattern}/"
        passed = content is not None and bool(pattern.search(content))
        found = "the text matches" if passed else "no match in the text"

    if content is None:
        found = f"no {path} at {at}"
    return AssertionResult(kind="file_content", passed=passed, want=want, found=found)


def _read_at(ctx: EvalContext, at: str, path: str) -> str | None:
    if ctx.blobs is None:
        raise LevelAuthoringError("file content predicates need blob access")
    if at == WORKTREE:
        return ctx.blobs.read_worktree(path)
    if at == INDEX:
        sha = ctx.snapshot.index_blobs.get(path)
        return None if sha is None else ctx.blobs.read_text(sha)
    return ctx.blobs.read_text(f"{resolve(ctx, at)}:{path}")


@register("status_clean", args=ArgsSpec(optional=("allow_untracked", "ignoring", "label")))
def status_clean(ctx: EvalContext, args: Mapping[str, Any]) -> AssertionResult:
    allow_untracked = bool(args.get("allow_untracked", False))

    ignoring = {str(p) for p in args.get("ignoring", [])}

    entries = [e for e in ctx.snapshot.status if e.path not in ignoring]
    dirty = [e for e in entries if e.kind in ("ordinary", "renamed", "unmerged")]
    untracked = [e for e in entries if e.kind == "untracked"]

    offenders = dirty if allow_untracked else dirty + untracked
    listing = ", ".join(e.path for e in offenders[:3]) or "nothing pending"
    if len(offenders) > 3:
        listing += f", and {len(offenders) - 3} more"
    return AssertionResult(
        kind="status_clean",
        passed=not offenders,
        want="working tree and index clean"
        + (" (untracked files allowed)" if allow_untracked else ""),
        found=listing,
    )


@register("file_staged", args=ArgsSpec(required=("path",), optional=("staged", "label")))
def file_staged(ctx: EvalContext, args: Mapping[str, Any]) -> AssertionResult:
    path = str(args["path"])
    want_staged = bool(args.get("staged", True))
    entry = next((e for e in ctx.snapshot.status if e.path == path), None)
    # A conflicted path carries an index status of U/A/D, which `is_staged`
    # reads as staged. It is not: there is no stage-0 entry at all, and
    # telling a student mid-conflict that their file is staged is a lie.
    if entry is not None and entry.kind == "unmerged":
        return AssertionResult(
            kind="file_staged",
            passed=not want_staged,
            want=f"{path} {'is' if want_staged else 'is not'} staged",
            found=f"{path} is conflicted, so nothing is staged for it yet",
        )

    actually_staged = entry is not None and entry.is_staged
    return AssertionResult(
        kind="file_staged",
        passed=actually_staged == want_staged,
        want=f"{path} {'is' if want_staged else 'is not'} staged",
        found=f"{path} is staged ({entry.index_status})"
        if actually_staged and entry
        else f"{path} has no staged changes",
    )


@register("remote_ref_at", args=ArgsSpec(required=("remote", "branch", "equals"),
                                         optional=("label",)))
def remote_ref_at(ctx: EvalContext, args: Mapping[str, Any]) -> AssertionResult:
    key = f"{args['remote']}/{args['branch']}"
    target = resolve(ctx, str(args["equals"]))
    sha = ctx.snapshot.remote_refs.get(key)
    return AssertionResult(
        kind="remote_ref_at",
        passed=sha == target,
        want=f"{key} at {args['equals']} ({_short(target)})",
        found=f"{key} -> {_short(sha)}" if sha else f"no remote-tracking ref {key}",
    )


def normalise_answer(text: str) -> str:
    """Strip the punctuation a student will reasonably include.

    Being told you are wrong when you are right is the fastest way to lose
    someone on level one, so `main`, "main" and main. all count as main.
    """
    # Smart quotes included: a student pasting from a rendered document or a
    # phone keyboard gets curly ones without choosing to.
    opening = "`'\"“”‘’"  # noqa: RUF001 - the curly quotes are the point
    closing = opening + ".,;:!?"
    stripped = text.strip()
    while stripped and stripped[0] in opening:
        stripped = stripped[1:]
    while stripped and stripped[-1] in closing:
        stripped = stripped[:-1]
    return stripped.strip()


@register(
    "answer",
    args=ArgsSpec(
        required=("id",),
        optional=("prompt", "label", "accepts"),
        one_of=(("equals", "equals_commit"),),
    ),
)
def answer(ctx: EvalContext, args: Mapping[str, Any]) -> AssertionResult:
    """A comprehension prompt, for levels that are deliberately read-only.

    Level 1.1 mutates nothing by design, so no state predicate can fire. Here
    the diagnosis itself is the graded act.
    """
    key = str(args["id"])
    given = normalise_answer(str(ctx.answers.get(key, "")))
    prompt = str(args.get("prompt", f"answer {key}"))

    if not given:
        return AssertionResult(
            kind="answer", passed=False, want=prompt,
            found="not answered yet — type your answer on the job sheet",
        )

    if "equals_commit" in args:
        return _answer_commit(ctx, args, key=key, given=given, prompt=prompt)

    accepted = [str(args["equals"]), *(str(a) for a in args.get("accepts", []))]
    passed = any(given.casefold() == candidate.casefold() for candidate in accepted)
    return AssertionResult(
        kind="answer", passed=passed, want=prompt, found=f"you answered {given!r}",
    )


def _answer_commit(
    ctx: EvalContext, args: Mapping[str, Any], *, key: str, given: str, prompt: str
) -> AssertionResult:
    """Accept any unambiguous prefix, exactly as git itself does."""
    from git_tutorial.errors import RefResolutionError
    from git_tutorial.predicates.resolve import resolve

    target = resolve(ctx, str(args["equals_commit"]))
    try:
        actual = resolve(ctx, given)
    except RefResolutionError as exc:
        return AssertionResult(
            kind="answer", passed=False, want=prompt,
            found=f"{given!r} does not name a commit in this repository",
            detail=str(exc),
        )
    return AssertionResult(
        kind="answer",
        passed=actual == target,
        want=prompt,
        found=f"you answered {given!r}" + ("" if actual == target else " — a different commit"),
    )


# -- technique: what was typed, not just what is left behind (spec 6.5) ------
#
# These read the reflog window the level opened at setup. They are
# technique-gated: under `technique: loose` they are evaluated and shown, so
# the student still learns what was noticed, but they do not block.


def _window(ctx: EvalContext, args: Mapping[str, Any]) -> tuple[GitEvent, ...]:
    """The level's own events on one ref, newest last.

    HEAD unless the level says otherwise, because a single commit writes a
    line to both `logs/HEAD` and `logs/refs/heads/<branch>` and counting
    both would make `at_least: 2` pass on one commit.
    """
    ref = str(args.get("on_ref", "HEAD"))
    if ref != "HEAD" and not ref.startswith("refs/"):
        ref = f"refs/heads/{ref}"
    window = reflog.since_offsets(tuple(ctx.events), ctx.level_start_offsets)
    ops = {str(op) for op in args["ops"]}
    return tuple(e for e in window if e.ref == ref and e.op in ops)


def _named(args: Mapping[str, Any]) -> str:
    return " or ".join(f"`git {op}`" for op in args["ops"])


_TECHNIQUE_ARGS = ArgsSpec(
    required=("ops",),
    optional=("at_least", "since", "on_ref", "label"),
    # `since` takes one value today. It is a choice rather than an ignored
    # string so that a level asking for a window this cannot provide fails
    # at load, instead of quietly grading the whole session.
    choices=(("ops", reflog.OPS), ("since", ("@level_start",))),
)


@register("used_command", args=_TECHNIQUE_ARGS, technique_gated=True)
def used_command(ctx: EvalContext, args: Mapping[str, Any]) -> AssertionResult:
    want = int(args.get("at_least", 1))
    found = _window(ctx, args)
    return AssertionResult(
        kind="used_command",
        passed=len(found) >= want,
        want=f"{_named(args)}, {want}x since this level began",
        found=f"{len(found)}x" if found else "not in the reflog for this level",
        detail=_trail(found) if found else None,
    )


@register("not_used_command", args=_TECHNIQUE_ARGS, technique_gated=True)
def not_used_command(ctx: EvalContext, args: Mapping[str, Any]) -> AssertionResult:
    found = _window(ctx, args)
    return AssertionResult(
        kind="not_used_command",
        passed=not found,
        want=f"{_named(args)} not used - this level is about the other way round",
        found="not used" if not found else f"used {len(found)}x",
        detail=_trail(found) if found else None,
    )


def _trail(events: tuple[GitEvent, ...]) -> str:
    """What git recorded, in git's words. A student disputing one of these
    can read the same lines with `git reflog`."""
    return "; ".join(f"{e.op}: {e.detail}" if e.detail else e.op for e in events[-3:])
