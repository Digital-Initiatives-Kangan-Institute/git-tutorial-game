from __future__ import annotations

from collections import deque
from collections.abc import Collection, Iterable, Iterator, Mapping
from dataclasses import dataclass
from types import MappingProxyType

from git_tutorial.errors import TutorialError


class GraphTruncated(TutorialError):
    """An ancestry walk ran off the edge of a capped graph.

    Never answer False in this case: a silent wrong answer presented
    confidently is worse than a loud engine error.
    """


@dataclass(frozen=True, slots=True)
class CommitNode:
    sha: str
    parents: tuple[str, ...]
    tree: str
    subject: str
    commit_time: int


class CommitGraph:
    __slots__ = ("_children", "_nodes", "truncated")

    def __init__(self, nodes: Mapping[str, CommitNode], *, truncated: bool = False) -> None:
        self._nodes: Mapping[str, CommitNode] = MappingProxyType(dict(nodes))
        self.truncated = truncated
        self._children: dict[str, frozenset[str]] | None = None

    @property
    def nodes(self) -> Mapping[str, CommitNode]:
        return self._nodes

    def __contains__(self, sha: str) -> bool:
        return sha in self._nodes

    def __len__(self) -> int:
        return len(self._nodes)

    def get(self, sha: str) -> CommitNode | None:
        return self._nodes.get(sha)

    def require(self, sha: str) -> CommitNode:
        node = self._nodes.get(sha)
        if node is None:
            if self.truncated:
                raise GraphTruncated(f"commit {sha[:12]} is outside the loaded graph")
            raise TutorialError(f"commit {sha[:12]} is not in the repository graph")
        return node

    def children(self, sha: str) -> frozenset[str]:
        if self._children is None:
            acc: dict[str, set[str]] = {}
            for node in self._nodes.values():
                for parent in node.parents:
                    acc.setdefault(parent, set()).add(node.sha)
            self._children = {k: frozenset(v) for k, v in acc.items()}
        return self._children.get(sha, frozenset())

    def ancestors(self, sha: str, *, first_parent: bool = False) -> Iterator[str]:
        """Yields sha then every commit reachable from it, breadth-first."""
        seen = {sha}
        queue = deque([sha])
        while queue:
            current = queue.popleft()
            yield current
            node = self._nodes.get(current)
            if node is None:
                if self.truncated:
                    raise GraphTruncated(f"walk left the loaded graph at {current[:12]}")
                continue
            parents = node.parents[:1] if first_parent else node.parents
            for parent in parents:
                if parent not in seen:
                    seen.add(parent)
                    queue.append(parent)

    def is_ancestor(self, ancestor: str, descendant: str) -> bool:
        if ancestor == descendant:
            return True
        return any(sha == ancestor for sha in self.ancestors(descendant))

    def merge_base(self, a: str, b: str) -> str | None:
        reachable_a = set(self.ancestors(a))
        candidates = [sha for sha in self.ancestors(b) if sha in reachable_a]
        if not candidates:
            return None
        # The best common ancestor is the one no other candidate can reach.
        candidate_set = set(candidates)
        for sha in candidates:
            others = candidate_set - {sha}
            if not any(self.is_ancestor(sha, other) for other in others):
                return sha
        return candidates[0]

    def topo_order(self, tips: Iterable[str]) -> list[str]:
        """Parents after children. Ties broken newest-first, then by sha."""
        included: set[str] = set()
        for tip in tips:
            if tip in self._nodes:
                included.update(self.ancestors(tip))

        indegree = {sha: 0 for sha in included}
        for sha in included:
            for parent in self._nodes[sha].parents:
                if parent in included:
                    indegree[parent] += 1

        ready = sorted(
            (s for s, deg in indegree.items() if deg == 0),
            key=self._sort_key,
        )
        out: list[str] = []
        while ready:
            sha = ready.pop(0)
            out.append(sha)
            for parent in self._nodes[sha].parents:
                if parent in indegree:
                    indegree[parent] -= 1
                    if indegree[parent] == 0:
                        ready.append(parent)
                        ready.sort(key=self._sort_key)
        return out

    def count_range(self, include: Collection[str], exclude: Collection[str] = ()) -> int:
        """`git rev-list A ^B` semantics."""
        excluded: set[str] = set()
        for sha in exclude:
            if sha in self._nodes:
                excluded.update(self.ancestors(sha))
        reachable: set[str] = set()
        for sha in include:
            if sha in self._nodes:
                reachable.update(self.ancestors(sha))
        return len(reachable - excluded)

    def _sort_key(self, sha: str) -> tuple[int, str]:
        node = self._nodes[sha]
        return (-node.commit_time, sha)


_FIELD_SEP = "\x1f"


def parse_rev_list(payload: str) -> CommitGraph:
    """Parses `rev-list --no-commit-header --format='%H%x1f%P%x1f%T%x1f%ct%x1f%s'`."""
    nodes: dict[str, CommitNode] = {}
    for line in payload.splitlines():
        if not line:
            continue
        parts = line.split(_FIELD_SEP, 4)
        if len(parts) != 5:
            continue
        sha, parents_raw, tree, ctime, subject = parts
        nodes[sha] = CommitNode(
            sha=sha,
            parents=tuple(parents_raw.split()) if parents_raw else (),
            tree=tree,
            subject=subject,
            commit_time=int(ctime),
        )
    return CommitGraph(nodes)
