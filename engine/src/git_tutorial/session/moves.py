"""Snapshots in, moves out — the watcher's memory of what just happened.

The warehouse module decides what a difference between two snapshots
means; this is the stateful half that remembers the previous snapshot and
where each reflog had got to, so both front ends see the same moves.
"""

from __future__ import annotations

from git_tutorial.git import reflog, supplier
from git_tutorial.git.probe import GitRepoProbe
from git_tutorial.git.snapshot import RepoSnapshot
from git_tutorial.scene import warehouse


class MoveTracker:
    def __init__(self, probe: GitRepoProbe) -> None:
        self.probe = probe
        self.move: warehouse.Move | None = None
        self.unseen: int | None = None
        self.office: supplier.HeadOffice | None = None
        self._seen: RepoSnapshot | None = None
        self._level: str | None = None
        self._offsets: dict[str, int] | None = None

    def observe(self, snapshot: RepoSnapshot, level_id: str | None) -> bool:
        """True when this snapshot brought a new move.

        A level change rebuilds the repository, so the comparison starts
        over rather than reporting the setup script's work as the student's.
        """
        if snapshot is self._seen:
            return False
        git_dir = self.probe.git_dir
        if level_id != self._level or self._offsets is None:
            self._seen, self._level, self.move = None, level_id, None
            self._offsets = reflog.offsets(git_dir)
        events, self._offsets = reflog.read_all(git_dir, since=self._offsets)
        office = supplier.head_office(self.probe.runner)
        before = self.office if self._seen is not None else None
        move = warehouse.detect_move(self._seen, snapshot, events, office=(before, office))
        self._seen = snapshot
        self.office = office
        self.unseen = supplier.unseen(self.probe.runner, snapshot)
        if move is None:
            return False
        self.move = move
        return True
