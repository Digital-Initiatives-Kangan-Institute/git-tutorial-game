from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from git_tutorial.git.snapshot import IN_PROGRESS_DIRS, IN_PROGRESS_FILES
from git_tutorial.predicates.base import ArgsSpec, AssertionResult, EvalContext, register
from git_tutorial.predicates.resolve import resolve

IN_PROGRESS_OPS = (*IN_PROGRESS_FILES, *IN_PROGRESS_DIRS)

OPERATION_NAMES = {
    "MERGE_HEAD": "merge",
    "MERGE_MSG": "merge",
    "CHERRY_PICK_HEAD": "cherry-pick",
    "REVERT_HEAD": "revert",
    "rebase-merge": "rebase",
    "rebase-apply": "rebase",
}


def _short(sha: str) -> str:
    return sha[:7]


def _compare(value: int, args: Mapping[str, Any]) -> tuple[bool, str]:
    if "exactly" in args:
        return value == int(args["exactly"]), f"exactly {args['exactly']}"
    if "at_least" in args:
        return value >= int(args["at_least"]), f"at least {args['at_least']}"
    return value <= int(args["at_most"]), f"at most {args['at_most']}"


@register("tag_exists", args=ArgsSpec(required=("name",), optional=("on", "label")))
def tag_exists(ctx: EvalContext, args: Mapping[str, Any]) -> AssertionResult:
    name = str(args["name"])
    sha = ctx.snapshot.tags.get(name)
    if "on" not in args:
        return AssertionResult(
            kind="tag_exists",
            passed=sha is not None,
            want=f"tag {name} exists",
            found=f"{name} -> {_short(sha)}" if sha else f"no tag {name}",
        )
    target = resolve(ctx, str(args["on"]))
    return AssertionResult(
        kind="tag_exists",
        passed=sha == target,
        want=f"tag {name} on {args['on']} ({_short(target)})",
        found=f"{name} -> {_short(sha)}" if sha else f"no tag {name}",
    )


@register("trees_equal", args=ArgsSpec(required=("a", "b"), optional=("label",)))
def trees_equal(ctx: EvalContext, args: Mapping[str, Any]) -> AssertionResult:
    """Content restored, regardless of the route taken to restore it."""
    graph = ctx.snapshot.graph
    tree_a = graph.require(resolve(ctx, str(args["a"]))).tree
    tree_b = graph.require(resolve(ctx, str(args["b"]))).tree
    return AssertionResult(
        kind="trees_equal",
        passed=tree_a == tree_b,
        want=f"{args['a']} has the same content as {args['b']}",
        found="trees match" if tree_a == tree_b else "tree differs",
    )


@register("file_absent", args=ArgsSpec(required=("path",), optional=("at", "label")))
def file_absent(ctx: EvalContext, args: Mapping[str, Any]) -> AssertionResult:
    from git_tutorial.predicates.core import _read_at

    path = str(args["path"])
    at = str(args.get("at", "WORKTREE"))
    content = _read_at(ctx, at, path)
    return AssertionResult(
        kind="file_absent",
        passed=content is None,
        want=f"{path} is gone from {at}",
        found="not there" if content is None else "still there",
    )


@register("stash_count", args=ArgsSpec(optional=("label",), one_of=(("exactly", "at_least"),)))
def stash_count(ctx: EvalContext, args: Mapping[str, Any]) -> AssertionResult:
    actual = ctx.snapshot.stash_count
    passed, want = _compare(actual, args)
    return AssertionResult(
        kind="stash_count",
        passed=passed,
        want=f"{want} stash entr(ies)",
        found=f"{actual} stashed" if actual else "the stash is empty",
    )


@register(
    "commit_count",
    args=ArgsSpec(
        required=("from",),
        optional=("not_from", "label"),
        one_of=(("exactly", "at_least", "at_most"),),
    ),
)
def commit_count(ctx: EvalContext, args: Mapping[str, Any]) -> AssertionResult:
    """`A ^B` semantics: commits reachable from `from` but not from `not_from`."""
    include = [resolve(ctx, str(args["from"]))]
    exclude = [resolve(ctx, str(args["not_from"]))] if "not_from" in args else []
    actual = ctx.snapshot.graph.count_range(include, exclude)
    passed, want = _compare(actual, args)
    scope = f"{args['from']}" + (f" not in {args['not_from']}" if exclude else "")
    return AssertionResult(
        kind="commit_count",
        passed=passed,
        want=f"{want} commit(s) in {scope}",
        found=f"{actual} commit(s)",
    )


@register("graph_linear", args=ArgsSpec(required=("from", "to"), optional=("label",)),
          technique_gated=True)
def graph_linear(ctx: EvalContext, args: Mapping[str, Any]) -> AssertionResult:
    start = resolve(ctx, str(args["to"]))
    stop = resolve(ctx, str(args["from"]))
    graph = ctx.snapshot.graph

    merges: list[str] = []
    for sha in graph.ancestors(start):
        if sha == stop:
            continue
        node = graph.get(sha)
        if node and len(node.parents) > 1:
            merges.append(sha)

    return AssertionResult(
        kind="graph_linear",
        passed=not merges,
        want=f"no merge commits between {args['from']} and {args['to']}",
        found="history is linear"
        if not merges
        else f"{len(merges)} merge commit(s): {', '.join(_short(s) for s in merges[:3])}",
    )


@register("conflicted", args=ArgsSpec(optional=("path", "expected", "label")))
def conflicted(ctx: EvalContext, args: Mapping[str, Any]) -> AssertionResult:
    """Which files are mid-merge and disagreeing.

    The porcelain-v2 `u` records were already parsed and had no way out to a
    level, so the only way to ask was to grep the worktree for `<<<<<<<` —
    which also matches a student who typed the markers into a document.
    """
    conflicts = sorted(e.path for e in ctx.snapshot.status if e.kind == "unmerged")
    expected = bool(args.get("expected", True))

    if "path" in args:
        path = str(args["path"])
        present = path in conflicts
        want = f"{path} {'is' if expected else 'is not'} conflicted"
    else:
        present = bool(conflicts)
        want = "a file is conflicted" if expected else "no file is conflicted"

    if conflicts:
        shown = ", ".join(conflicts[:3])
        found = f"conflicted: {shown}" + ("..." if len(conflicts) > 3 else "")
    else:
        found = "nothing is conflicted"

    return AssertionResult(
        kind="conflicted", passed=present == expected, want=want, found=found
    )


@register(
    "in_progress",
    # Without the choices check, `op: merge` (rather than MERGE_HEAD) is never
    # present, so `expected: false` passes in every repository on earth - a
    # level that can never fail and never says so.
    args=ArgsSpec(required=("op",), optional=("expected", "label"),
                  choices=(("op", IN_PROGRESS_OPS),)),
)
def in_progress(ctx: EvalContext, args: Mapping[str, Any]) -> AssertionResult:
    op = str(args["op"])
    expected = bool(args.get("expected", True))
    present = op in ctx.snapshot.in_progress
    # The marker is a filename inside .git, which is no use to a student
    # reading the scoreboard. Name the operation it stands for.
    english = OPERATION_NAMES.get(op, op)
    return AssertionResult(
        kind="in_progress",
        passed=present == expected,
        want=f"a {english} {'is' if expected else 'is not'} in progress",
        found=f"a {english} is paused part way" if present
        else f"no {english} in progress",
    )


@register("ahead_behind", args=ArgsSpec(required=("branch", "upstream"),
                                        optional=("ahead", "behind", "label")))
def ahead_behind(ctx: EvalContext, args: Mapping[str, Any]) -> AssertionResult:
    branch = str(args["branch"])
    upstream = str(args["upstream"])
    graph = ctx.snapshot.graph

    local = ctx.snapshot.branches.get(branch)
    # Act 2 asks how far a feature branch has diverged from main, and both
    # sides of that are local. Remote-tracking names win, so `origin/main`
    # still means the remote even if a local branch is named that way.
    remote = ctx.snapshot.remote_refs.get(upstream) or ctx.snapshot.branches.get(upstream)
    if local is None or remote is None:
        missing = branch if local is None else upstream
        return AssertionResult(
            kind="ahead_behind",
            passed=False,
            want=f"{branch} compared against {upstream}",
            found=f"{missing} does not exist",
        )

    ahead = graph.count_range([local], [remote])
    behind = graph.count_range([remote], [local])

    wants: list[str] = []
    passed = True
    if "ahead" in args:
        wants.append(f"{args['ahead']} ahead")
        passed = passed and ahead == int(args["ahead"])
    if "behind" in args:
        wants.append(f"{args['behind']} behind")
        passed = passed and behind == int(args["behind"])

    return AssertionResult(
        kind="ahead_behind",
        passed=passed,
        want=f"{branch} is {' and '.join(wants) or 'compared'} vs {upstream}",
        found=f"{ahead} ahead, {behind} behind",
    )


@register("worktree_unchanged", args=ArgsSpec(required=("paths",), optional=("label",)))
def worktree_unchanged(ctx: EvalContext, args: Mapping[str, Any]) -> AssertionResult:
    """Guards against solving a recovery level by retyping the file by hand."""
    paths = [str(p) for p in args["paths"]]
    baseline = ctx.level_start_worktree

    edited: list[str] = []
    for path in paths:
        before = baseline.get(path)
        now = ctx.snapshot.worktree_blobs.get(path) or ctx.snapshot.index_blobs.get(path)
        if before is not None and now is not None and before != now:
            edited.append(path)

    return AssertionResult(
        kind="worktree_unchanged",
        passed=not edited,
        want=f"{', '.join(paths)} recovered, not hand-edited",
        found="untouched since the level began"
        if not edited
        else f"edited by hand: {', '.join(edited)}",
    )


@register("tracks", args=ArgsSpec(required=("branch",), optional=("upstream", "label")))
def tracks(ctx: EvalContext, args: Mapping[str, Any]) -> AssertionResult:
    """Does this branch have an upstream, and is it the expected one?

    `ahead_behind` is told which upstream to compare against, so it cannot
    answer this: a branch pushed without `-u` is zero ahead and zero behind
    the remote ref that now exists, and the row passes while the student's
    next bare `git push` still fails. This reads the configuration itself.
    """
    branch = str(args["branch"])
    actual = ctx.snapshot.upstream.get(branch)
    wanted = str(args["upstream"]) if "upstream" in args else None

    return AssertionResult(
        kind="tracks",
        passed=bool(actual) and (wanted is None or actual == wanted),
        want=(
            f"{branch} set to track {wanted}" if wanted
            else f"{branch} tracking a branch on the remote"
        ),
        found=f"{branch} tracks {actual}" if actual else f"{branch} tracks nothing",
    )


@register(
    "head_office_ref",
    args=ArgsSpec(required=("ref",), optional=("exists", "at", "label")),
)
def head_office_ref(ctx: EvalContext, args: Mapping[str, Any]) -> AssertionResult:
    """What Head Office (origin) really holds, not what this clone last heard.

    `git push origin --delete x` and pushing a tag change only the remote, so
    the local snapshot cannot grade them. Read-only, and only for an origin on
    this disk, which the tutorial's always is.
    """
    from git_tutorial.errors import LevelAuthoringError
    from git_tutorial.git import supplier

    ref = str(args["ref"])
    want_exists = bool(args.get("exists", True))
    if ctx.blobs is None:
        raise LevelAuthoringError("head_office_ref needs a repository to read origin from")
    office = supplier.head_office(ctx.blobs.runner)
    if office is None:
        raise LevelAuthoringError("head_office_ref: origin is not a repository on this disk")

    kind, _, name = ref.removeprefix("refs/").partition("/")
    table = {"heads": office.branches, "tags": office.tags}.get(kind)
    if table is None:
        raise LevelAuthoringError(f"head_office_ref: {ref!r} is not under refs/heads or refs/tags")
    sha = table.get(name)
    label = f"{'branch' if kind == 'heads' else 'tag'} {name}"
    found = f"Head Office has {label} at {_short(sha)}" if sha else f"Head Office has no {label}"

    if not want_exists:
        return AssertionResult(kind="head_office_ref", passed=sha is None,
                               want=f"no {label} at Head Office", found=found)
    if "at" not in args:
        return AssertionResult(kind="head_office_ref", passed=sha is not None,
                               want=f"{label} at Head Office", found=found)
    target = resolve(ctx, str(args["at"]))
    return AssertionResult(
        kind="head_office_ref", passed=sha == target,
        want=f"{label} at Head Office on {args['at']} ({_short(target)})", found=found,
    )


_MARKER = r"^(<<<<<<<|>>>>>>>)( |$)"


@register("no_conflict_markers", args=ArgsSpec(optional=("at", "paths", "label")))
def no_conflict_markers(ctx: EvalContext, args: Mapping[str, Any]) -> AssertionResult:
    """No `<<<<<<<` or `>>>>>>>` lines committed anywhere.

    A level that checks one file for markers misses the second file the
    student forgot. This greps the whole commit, the way git would show it.
    """
    from git_tutorial.errors import LevelAuthoringError

    if ctx.blobs is None:
        raise LevelAuthoringError("no_conflict_markers needs a repository to search")
    at = str(args.get("at", "HEAD"))
    rev = resolve(ctx, at)
    paths = [str(p) for p in args.get("paths", [])]
    found = ctx.blobs.runner.run(
        "grep", "-n", "-E", _MARKER, rev, "--", *paths, check=False,
    )
    hits = [line.split(":", 2)[1] for line in found.stdout.splitlines() if line.count(":") >= 2]
    files = sorted(set(hits))
    return AssertionResult(
        kind="no_conflict_markers",
        passed=not files,
        want=f"no conflict markers committed at {at}",
        found="none" if not files else "markers in " + ", ".join(files),
    )


@register("file_matches", args=ArgsSpec(required=("path", "against"), optional=("at", "label")))
def file_matches(ctx: EvalContext, args: Mapping[str, Any]) -> AssertionResult:
    """A file is exactly as it is at another commit: "took their side whole"."""
    from git_tutorial.errors import LevelAuthoringError

    if ctx.blobs is None:
        raise LevelAuthoringError("file_matches needs blob access")
    path = str(args["path"])
    at = str(args.get("at", "HEAD"))
    against = str(args["against"])
    mine = ctx.blobs.read_text(f"{resolve(ctx, at)}:{path}")
    other = ctx.blobs.read_text(f"{resolve(ctx, against)}:{path}")
    if other is None:
        raise LevelAuthoringError(f"file_matches: {path} does not exist at {against}")
    if mine is None:
        found = f"no {path} at {at}"
    elif mine == other:
        found = f"{path} at {at} is the {against} version exactly"
    else:
        found = f"{path} at {at} differs from {against}"
    return AssertionResult(kind="file_matches", passed=mine == other,
                           want=f"{path} at {at} matches {against}", found=found)
