"""The warehouse picture: the repository as the browser draws it.

A plain dict, so it goes over the wire as JSON and the page holds no git
knowledge of its own. Every crate is keyed by its full sha and every file
by its path: the page animates an element that changes zone by finding
the same key where it was before, so a pushed commit visibly travels from
the local shelf to Head Office's.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from git_tutorial.git.graph import GraphTruncated
from git_tutorial.git.snapshot import RepoSnapshot
from git_tutorial.git.supplier import HeadOffice
from git_tutorial.scene import warehouse

CRATES = 6  # per shelf, newest last
SHELVES = 5  # local branches drawn before the rest are summarised
YARD = 6


def picture(
    snapshot: RepoSnapshot,
    *,
    unseen: int | None,
    hidden: frozenset[str] = frozenset(),
    office: HeadOffice | None = None,
    remembered: frozenset[str] | None = None,
    worktree: Path | None = None,
    git_dir: Path | None = None,
) -> dict[str, Any]:
    scene = warehouse.build_scene(snapshot, unseen=unseen)

    names = sorted(snapshot.branches, key=lambda b: (b != snapshot.head_ref, b))
    shelves = [_shelf(snapshot, name) for name in names[:SHELVES]]

    tracked = sorted({up for up in snapshot.upstream.values()} & set(snapshot.remote_refs))
    others = sorted(r for r in snapshot.remote_refs if r not in tracked and not r.endswith("/HEAD"))
    remotes = [
        {
            "name": name,
            "crates": _crates(snapshot, snapshot.remote_refs[name]),
            # Head Office deleted it; only this clone's note of it remains,
            # until `git fetch --prune` takes the note down.
            "stale": office is not None and name.partition("/")[2] not in office.branches,
        }
        for name in [*tracked, *others][:SHELVES]
    ]

    return {
        "floor": [_floor_item(i, worktree) for i in scene.floor],
        "bench": [{"path": i.path, "mark": i.mark} for i in scene.bench],
        "head": {
            "branch": snapshot.head_ref,
            "sha": snapshot.head_sha,
            "detached": snapshot.detached,
        },
        "shelves": shelves,
        "more_shelves": max(0, len(names) - SHELVES),
        "upstream": scene.upstream,
        "ahead": scene.ahead,
        "behind": scene.behind,
        "remotes": remotes,
        "unseen": unseen,
        "stash": scene.stash,
        "yard": _yard(snapshot, hidden, remembered),
        "hold": scene.hold,
        "hold_from": _hold_from(git_dir) if scene.hold else None,
        "tags": [{"name": n, "sha": sha} for n, sha in sorted(snapshot.tags.items())],
        "office": None if office is None else {
            "branches": sorted(office.branches),
            "tags": [
                {"name": n, "sha": sha, "short": sha[: warehouse.SHORT]}
                for n, sha in sorted(office.tags.items())
            ],
        },
    }


def _floor_item(item: warehouse.Item, worktree: Path | None) -> dict[str, Any]:
    out: dict[str, Any] = {"path": item.path, "mark": item.mark}
    if item.mark == "!":
        out["detail"] = item.detail
        out["blocks"] = _blocks(worktree, item.path)
    return out


def _blocks(worktree: Path | None, path: str) -> int | None:
    """Disputed blocks still in a held file: the count falls as you edit."""
    if worktree is None:
        return None
    try:
        text = (worktree / path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0  # gone from disk: a modify/delete with nothing to edit
    return sum(1 for line in text.splitlines() if line.startswith("<<<<<<<"))


def _hold_from(git_dir: Path | None) -> str:
    """"pull" when the paused merge is one `git pull` started."""
    if git_dir is None:
        return "merge"
    try:
        first = (git_dir / "MERGE_MSG").read_text(encoding="utf-8").splitlines()[0]
    except (OSError, IndexError):
        return "merge"
    return "pull" if re.match(r"Merge branch '[^']+' of ", first) else "merge"


def _shelf(snapshot: RepoSnapshot, name: str) -> dict[str, Any]:
    return {
        "name": name,
        "head": name == snapshot.head_ref,
        "upstream": snapshot.upstream.get(name),
        "crates": _crates(snapshot, snapshot.branches[name]),
    }


def _crate(snapshot: RepoSnapshot, sha: str) -> dict[str, Any]:
    node = snapshot.graph.get(sha)
    return {
        "sha": sha,
        "short": sha[: warehouse.SHORT],
        "subject": node.subject if node else "",
        "merge": bool(node and len(node.parents) > 1),
    }


def _crates(snapshot: RepoSnapshot, tip: str) -> list[dict[str, Any]]:
    if tip not in snapshot.graph:
        return []
    line: list[str] = []
    try:
        for sha in snapshot.graph.ancestors(tip, first_parent=True):
            line.append(sha)
            if len(line) == CRATES:
                break
    except GraphTruncated:
        pass
    return [_crate(snapshot, sha) for sha in reversed(line)]


def _yard(snapshot: RepoSnapshot, hidden: frozenset[str],
          remembered: frozenset[str] | None) -> list[dict[str, Any]]:
    """Unreachable commits a reflog still records, newest first.

    That is exactly what the yard's caption claims. A commit some reflog
    names counts, and so do its unreachable ancestors (a `reset --hard
    HEAD~3` records only the old tip). Commits that only a pruned or
    deleted remote branch knew are not the student's loss and are left out.
    """
    lost_shas = set(warehouse.unreachable(snapshot)) - hidden
    if remembered is not None:
        kept: set[str] = set()
        queue = [sha for sha in lost_shas if sha in remembered]
        while queue:
            sha = queue.pop()
            if sha in kept:
                continue
            kept.add(sha)
            node = snapshot.graph.get(sha)
            queue.extend(p for p in (node.parents if node else ()) if p in lost_shas)
        lost_shas = kept
    lost = [snapshot.graph.require(sha) for sha in lost_shas]
    lost.sort(key=lambda n: (-n.commit_time, n.sha))
    return [_crate(snapshot, n.sha) for n in lost[:YARD]]
