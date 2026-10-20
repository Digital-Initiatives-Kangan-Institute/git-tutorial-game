"""The warehouse scene: where everything is, and what just moved.

The local repository is drawn as a warehouse and origin as Head Office, but
every zone, crate and arrow carries the git term the student types — the
picture is the flavour, the words stay real.

Pure: snapshots in, data out. Movement is worked out by comparing two
snapshots rather than from the reflog alone, because `git add` writes no
reflog line and it is the first move every student makes. The reflog only
names the command when a ref moved.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from git_tutorial.git.graph import GraphTruncated
from git_tutorial.git.reflog import GitEvent
from git_tutorial.git.snapshot import RepoSnapshot
from git_tutorial.git.supplier import HeadOffice
from git_tutorial.predicates.extended import OPERATION_NAMES

SHORT = 7  # the width `git log --oneline` prints, so the two can be compared


@dataclass(frozen=True, slots=True)
class Item:
    path: str
    mark: str  # "+" added, "~" modified, "-" deleted, "?" untracked, "!" conflicted
    detail: str = ""  # for "!": what kind of dispute, in plain words


# git's two-letter code for an unmerged path, as the student would say it.
CONFLICT_KINDS = {
    "UU": "both changed",
    "AA": "added by both",
    "UD": "deleted by them",
    "DU": "deleted by you",
    "AU": "added by you",
    "UA": "added by them",
    "DD": "deleted by both",
}

NO_BLOB = "0" * 40


@dataclass(frozen=True, slots=True)
class Scene:
    floor: tuple[Item, ...]  # working tree
    bench: tuple[Item, ...]  # staging area
    shelf: str | None  # the branch HEAD is on; None when detached
    crates: tuple[str, ...]  # HEAD's first-parent line, newest last
    other_shelves: tuple[str, ...]
    upstream: str | None  # "origin/main"
    supplier_crates: tuple[str, ...]
    ahead: int
    behind: int
    unseen: int | None  # on the supplier, not yet fetched; None when unknown
    stash: int
    hold: str | None  # the paused operation, in words
    yard: int  # commits only the reflog still reaches


@dataclass(frozen=True, slots=True)
class Move:
    """What just went where, named by the command that moved it."""

    command: str  # "git add"
    source: str  # "working tree"
    dest: str  # "staging area"
    detail: str = ""


# --- the scene ---------------------------------------------------------------


def build_scene(snapshot: RepoSnapshot, *, unseen: int | None = None,
                crates: int = 4) -> Scene:
    floor: list[Item] = []
    bench: list[Item] = []
    for entry in snapshot.status:
        if entry.kind == "ignored":
            continue
        if entry.kind == "untracked":
            floor.append(Item(entry.path, "?"))
            continue
        if entry.kind == "unmerged":
            code = entry.index_status + entry.worktree_status
            floor.append(Item(entry.path, "!", CONFLICT_KINDS.get(code, "in conflict")))
            continue
        if entry.is_staged:
            bench.append(Item(entry.path, _mark(entry.index_status)))
        if entry.is_dirty:
            floor.append(Item(entry.path, _mark(entry.worktree_status)))

    upstream = snapshot.upstream.get(snapshot.head_ref) if snapshot.head_ref else None
    ahead, behind = snapshot.ahead_behind or (0, 0)
    paused = sorted({OPERATION_NAMES.get(m, m) for m in snapshot.in_progress})

    return Scene(
        floor=tuple(floor),
        bench=tuple(bench),
        shelf=snapshot.head_ref,
        crates=_line(snapshot, snapshot.head_sha, crates),
        other_shelves=tuple(sorted(b for b in snapshot.branches if b != snapshot.head_ref)),
        upstream=upstream,
        supplier_crates=_line(snapshot, snapshot.remote_refs.get(upstream or ""), crates),
        ahead=ahead,
        behind=behind,
        unseen=unseen,
        stash=snapshot.stash_count,
        hold=", ".join(paused) or None,
        yard=len(unreachable(snapshot)),
    )


def _mark(code: str) -> str:
    return {"A": "+", "D": "-"}.get(code, "~")


def _line(snapshot: RepoSnapshot, tip: str | None, count: int) -> tuple[str, ...]:
    if not tip or tip not in snapshot.graph:
        return ()
    out: list[str] = []
    try:
        for sha in snapshot.graph.ancestors(tip, first_parent=True):
            out.append(sha)
            if len(out) == count:
                break
    except GraphTruncated:
        pass
    return tuple(reversed(out))


def unreachable(snapshot: RepoSnapshot) -> list[str]:
    """Commits in the graph that no branch, tag or remote reaches.

    The graph is loaded with --reflog, so these are exactly the commits a
    `reset --hard` or an amend left behind — Act 3's material. A stash is
    stored as commits too, and refs/stash is not among the tips, so with a
    stash present the answer would be wrong; it is empty then.
    """
    if snapshot.stash_count:
        return []
    # ORIG_HEAD is left out on purpose: it is the undo pointer a reset just
    # set, and counting it would hide the very commits the reset dropped.
    paused = [sha for name, sha in snapshot.special_refs.items() if name != "ORIG_HEAD"]
    tips = [*snapshot.tips().values(), *snapshot.tags.values(), *paused]
    reachable: set[str] = set()
    try:
        for tip in tips:
            if tip in snapshot.graph and tip not in reachable:
                reachable.update(snapshot.graph.ancestors(tip))
    except GraphTruncated:
        return []
    return [sha for sha in snapshot.graph.nodes if sha not in reachable]


# --- movement ----------------------------------------------------------------

_COMMANDS = {
    "checkout": "git switch",
    "commit (amend)": "git commit --amend",
    "rebase (start)": "git rebase",
    "rebase (pick)": "git rebase",
    "rebase (finish)": "git rebase",
}


def _command(op: str) -> str:
    if op in _COMMANDS:
        return _COMMANDS[op]
    return "git " + op.split(" ", 1)[0]


def _plural(count: int, noun: str) -> str:
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"


def _last_op(events: Sequence[GitEvent], ref: str) -> str | None:
    ops = [e.op for e in events if e.ref == ref]
    return ops[-1] if ops else None


def detect_move(
    prev: RepoSnapshot | None,
    curr: RepoSnapshot,
    events: Sequence[GitEvent] = (),
    *,
    office: tuple[HeadOffice | None, HeadOffice | None] = (None, None),
) -> Move | None:
    """The one move that best explains the difference between two snapshots.

    Ref moves outrank file moves: a `git commit -am` empties the working
    tree as a side effect, and the commit is the thing to show. `office` is
    what Head Office held before and after, when it can be read: deleting a
    branch there and pushing a tag change nothing in this repository.
    """
    if prev is None:
        return None
    before, after = office
    found = _office_move(prev, curr, before, after)
    if found is not None:
        return found
    for detect in (_remote_move, _head_move, _branch_gone, _tag_move,
                   _hold_move, _stash_move, _conflict_move, _file_move):
        move = detect(prev, curr, events)
        if move is not None:
            return move
    return None


def _office_move(prev: RepoSnapshot, curr: RepoSnapshot,
                 before: HeadOffice | None, after: HeadOffice | None) -> Move | None:
    """Changes only Head Office can show: a pushed tag, a deleted branch,
    and a stale origin/* name pruned away."""
    if before is not None and after is not None:
        for name, sha in sorted(after.tags.items()):
            if before.tags.get(name) != sha and curr.tags.get(name) == sha:
                return Move("git push", f"tag {name}", "origin",
                            f"the seal on {sha[:SHORT]} is at Head Office now")
        for name in sorted(set(before.branches) - set(after.branches)):
            if f"origin/{name}" in prev.remote_refs and f"origin/{name}" not in curr.remote_refs:
                return Move("git push --delete", f"origin/{name}", "",
                            f"branch {name} deleted at Head Office")
    for ref in sorted(set(prev.remote_refs) - set(curr.remote_refs)):
        if ref.endswith("/HEAD"):
            continue
        branch = ref.partition("/")[2]
        if after is not None and branch in after.branches:
            continue  # still at Head Office: not a prune
        gone_before = before is None or branch not in before.branches
        if gone_before:
            return Move("git fetch --prune", ref, "",
                        f"Head Office had already deleted {branch}; the stale name is gone")
    return None


def _branch_gone(prev: RepoSnapshot, curr: RepoSnapshot,
                 events: Sequence[GitEvent]) -> Move | None:
    gone = sorted(set(prev.branches) - set(curr.branches))
    if not gone or prev.head_ref == gone[0]:
        return None
    name = gone[0]
    return Move("git branch -d", f"branch {name}", "",
                "the branch name is gone; its commits stay wherever other branches reach them")


def _tag_move(prev: RepoSnapshot, curr: RepoSnapshot,
              events: Sequence[GitEvent]) -> Move | None:
    for name, sha in sorted(curr.tags.items()):
        if prev.tags.get(name) != sha:
            return Move("git tag", "", f"tag {name}", f"sealed {sha[:SHORT]}")
    for name in sorted(set(prev.tags) - set(curr.tags)):
        return Move("git tag -d", f"tag {name}", "", "the seal is removed; the commit stays")
    return None


def _remote_move(prev: RepoSnapshot, curr: RepoSnapshot,
                 events: Sequence[GitEvent]) -> Move | None:
    for name, sha in sorted(curr.remote_refs.items()):
        old = prev.remote_refs.get(name)
        if name.endswith("/HEAD") or old == sha:
            continue
        count = curr.graph.count_range([sha], [old] if old else [])
        op = _last_op(events, f"refs/remotes/{name}")
        # A push records "update by push". Without the reflog line, a commit
        # we already had locally can only have reached the remote from here.
        if op == "update" or (op is None and sha in prev.graph):
            local = next((b for b, up in curr.upstream.items() if up == name), curr.head_ref)
            return Move("git push", f"branch {local}", name, f"{_plural(count, 'commit')} sent")
        if curr.in_progress and not prev.in_progress:
            # A pull whose merge stopped: the fetch half worked, the merge
            # half is waiting on the student.
            return Move("git pull", name, "paused",
                        f"{_plural(count, 'commit')} fetched; the merge stopped on a conflict")
        if curr.head_sha != prev.head_sha and _last_op(events, "HEAD") == "pull":
            return Move("git pull", name, f"branch {curr.head_ref}",
                        f"{_plural(count, 'commit')} fetched and merged")
        return Move("git fetch", "origin", name,
                    f"{_plural(count, 'commit')} fetched, not on your branch yet")
    return None


def _head_move(prev: RepoSnapshot, curr: RepoSnapshot,
               events: Sequence[GitEvent]) -> Move | None:
    if prev.head_sha == curr.head_sha and prev.head_ref == curr.head_ref:
        return None
    op = _last_op(events, "HEAD")
    here = f"branch {curr.head_ref}" if curr.head_ref else "HEAD (detached)"

    if curr.head_ref != prev.head_ref and op in (None, "checkout"):
        was = f"branch {prev.head_ref}" if prev.head_ref else "HEAD (detached)"
        return Move("git switch", was, here, "HEAD moved")

    node = curr.graph.get(curr.head_sha)
    if op is None:
        if node is not None and prev.head_sha in node.parents:
            op = "commit"
        elif prev.head_sha in curr.graph and curr.graph.is_ancestor(curr.head_sha, prev.head_sha):
            op = "reset"
    short = curr.head_sha[:SHORT]

    if op == "commit (amend)":
        return Move("git commit --amend", "staging area", here,
                    f"{short} replaces the old commit")
    if op is not None and op.startswith("commit"):
        return Move("git commit", "staging area", here, f"new commit {short}")
    if op == "reset":
        dropped = curr.graph.count_range([prev.head_sha], [curr.head_sha])
        if not dropped:
            return Move("git reset", here, here, f"now at {short}")
        detail = f"{_plural(dropped, 'commit')} off the branch"
        # Only commits nothing else reaches are in the yard. A reset past
        # commits that are already pushed leaves them on origin/main, and
        # saying "reflog only" there would be untrue.
        lost = set(unreachable(curr))
        if prev.head_sha in lost:
            return Move("git reset", here, "reflog only", detail)
        return Move("git reset", here, "off the branch", detail + ", still reachable elsewhere")
    if op is None:
        return Move("HEAD moved", "", here, f"now at {short}")
    return Move(_command(op), "", here, f"now at {short}")


def _hold_move(prev: RepoSnapshot, curr: RepoSnapshot,
               events: Sequence[GitEvent]) -> Move | None:
    started = curr.in_progress - prev.in_progress
    if started:
        name = sorted({OPERATION_NAMES.get(m, m) for m in started})[0]
        return Move(f"git {name}", "", "paused", "a conflict to resolve: finish it, or abort it")
    if prev.in_progress and not curr.in_progress:
        return Move("abort", "paused", "", "the operation was abandoned")
    return None


def _stash_move(prev: RepoSnapshot, curr: RepoSnapshot,
                events: Sequence[GitEvent]) -> Move | None:
    if curr.stash_count > prev.stash_count:
        return Move("git stash", "working tree", "stash", "changes put aside")
    if curr.stash_count < prev.stash_count:
        return Move("git stash pop", "stash", "working tree", "changes brought back")
    return None


def _conflict_move(prev: RepoSnapshot, curr: RepoSnapshot,
                   events: Sequence[GitEvent]) -> Move | None:
    """Settling a held file: removing it, taking one side whole, or adding it."""
    was = {e.path: e for e in prev.status if e.kind == "unmerged"}
    now = {e.path: e for e in curr.status}
    for path, held in sorted(was.items()):
        after = now.get(path)
        ours, theirs = held.unmerged_stages[1], held.unmerged_stages[2]
        if after is None or after.kind != "unmerged":
            if path not in curr.index_blobs:
                return Move("git rm", "inspection", "staging area",
                            f"{path} removed: the deletion is what gets committed")
            return Move("git add", "inspection", "staging area", f"conflict settled in {path}")
        content = curr.worktree_blobs.get(path)
        if content != prev.worktree_blobs.get(path):
            if content == theirs and theirs != NO_BLOB:
                return Move("git restore --theirs", "origin", "working tree",
                            f"{path} is their version whole; `git add` settles it")
            if content == ours and ours != NO_BLOB:
                return Move("git restore --ours", "", "working tree",
                            f"{path} is your version whole; `git add` settles it")
    for path in sorted(set(prev.index_blobs) - set(curr.index_blobs) - set(was)):
        staged = now.get(path)
        if staged is not None and staged.index_status == "D":
            return Move("git rm", "working tree", "staging area",
                        f"{path} removed: the deletion is staged for the next commit")
    return None


def _file_move(prev: RepoSnapshot, curr: RepoSnapshot,
               events: Sequence[GitEvent]) -> Move | None:
    before, after = build_scene(prev), build_scene(curr)
    staged = _paths(after.bench) - _paths(before.bench)
    unstaged = _paths(before.bench) - _paths(after.bench)
    edited = {i.path for i in after.floor if i not in before.floor}
    cleaned = _paths(before.floor) - _paths(after.floor) - staged

    if staged:
        return Move("git add", "working tree", "staging area", _files(staged))
    if unstaged:
        return Move("git restore --staged", "staging area", "working tree", _files(unstaged))
    if cleaned and not edited:
        return Move("git restore", "working tree", "last commit",
                    _files(cleaned) + " discarded")
    if edited:
        # No command moved this: the student's editor did. Showing it still
        # helps, because it is the change `git status` is about to report.
        return Move("edited", "", "working tree", _files(edited))
    return None


def _paths(items: Sequence[Item]) -> set[str]:
    return {i.path for i in items}


def _files(paths: set[str]) -> str:
    names = sorted(paths)
    if len(names) == 1:
        return names[0]
    return f"{len(names)} files: {', '.join(names[:2])}{', ...' if len(names) > 2 else ''}"
