from __future__ import annotations

import re
from typing import Final

from git_tutorial.errors import RefResolutionError
from git_tutorial.git.graph import GraphTruncated
from git_tutorial.predicates.base import EvalContext


class RefNotYetPresent(RefResolutionError):
    """A plain ref name that does not exist — yet.

    Distinct from a broken level. Most levels ask the student to create a
    branch, so "rescue does not exist" is the ordinary opening state and must
    read as an unfinished assertion, not as "this level is misconfigured".
    A tutorial: handle or @start failing to resolve is still an authoring error,
    because only the content can be at fault for those.
    """

# Sentinels accepted only by content predicates (spec 6.2).
WORKTREE: Final = "WORKTREE"
INDEX: Final = "INDEX"
CONTENT_SOURCES: Final = frozenset({WORKTREE, INDEX})

_SUFFIX = re.compile(r"(~|\^)(\d*)")
_SHA = re.compile(r"^[0-9a-f]{4,64}$")

_START_ALIASES = frozenset({"@start", "@level_start"})


def resolve(ctx: EvalContext, ref: str) -> str:
    """Resolves a commit-ref to a sha.

    Failure is a level authoring error, never a student failure.
    """
    if ref in CONTENT_SOURCES:
        raise RefResolutionError(
            f"{ref} is a content source and cannot be used where a commit is expected"
        )

    base, suffixes = _split(ref)
    sha = _resolve_base(ctx, base, original=ref)

    for op, count_raw in suffixes:
        count = int(count_raw) if count_raw else 1
        sha = _apply(ctx, sha, op, count, original=ref)
    return sha


def _split(ref: str) -> tuple[str, list[tuple[str, str]]]:
    match = _SUFFIX.search(ref)
    if match is None:
        return ref, []
    base = ref[: match.start()]
    return base, [(m.group(1), m.group(2)) for m in _SUFFIX.finditer(ref, match.start())]


def _resolve_base(ctx: EvalContext, base: str, *, original: str) -> str:
    snap = ctx.snapshot

    if base in _START_ALIASES:
        if ctx.level_start_sha is None:
            raise RefResolutionError(f"{original}: no level-start commit was recorded")
        return ctx.level_start_sha

    if base == "HEAD":
        return snap.head_sha

    if base.startswith("tutorial:"):
        name = base[len("tutorial:") :]
        try:
            return snap.tutorial_refs[name]
        except KeyError:
            known = ", ".join(sorted(snap.tutorial_refs)) or "(none present)"
            raise RefResolutionError(
                f"{original}: no tutorial ref {name!r}. Present: {known}. "
                "The practice history bundle may not have been unpacked."
            ) from None

    if base in snap.special_refs:
        return snap.special_refs[base]

    if base in snap.branches:
        return snap.branches[base]

    if base in snap.remote_refs:
        return snap.remote_refs[base]

    if base in snap.tags:
        return snap.tags[base]

    if _SHA.match(base):
        if base in snap.graph:
            return base
        matches = [sha for sha in snap.graph.nodes if sha.startswith(base)]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise RefResolutionError(f"{original}: ambiguous abbreviated sha")

    raise RefNotYetPresent(f"{base} does not exist yet")


def _apply(ctx: EvalContext, sha: str, op: str, count: int, *, original: str) -> str:
    graph = ctx.snapshot.graph
    try:
        if op == "~":
            for _ in range(count):
                node = graph.require(sha)
                if not node.parents:
                    raise RefResolutionError(f"{original}: walked past the root commit")
                sha = node.parents[0]
            return sha

        node = graph.require(sha)
        if count == 0:
            return sha
        if count > len(node.parents):
            raise RefResolutionError(
                f"{original}: commit {sha[:8]} has {len(node.parents)} parent(s), wanted #{count}"
            )
        return node.parents[count - 1]
    except GraphTruncated as exc:
        raise RefResolutionError(f"{original}: {exc}") from exc


def try_resolve(ctx: EvalContext, ref: str) -> str | None:
    try:
        return resolve(ctx, ref)
    except RefResolutionError:
        return None
