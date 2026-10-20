from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from git_tutorial.answers import AnswerSlot, slots_for
from git_tutorial.checker import Checker, CheckReport
from git_tutorial.errors import TutorialError
from git_tutorial.git import reflog, supplier
from git_tutorial.git.probe import GitRepoProbe
from git_tutorial.git.snapshot import RepoSnapshot
from git_tutorial.levels.model import AssertionSpec, Level
from git_tutorial.levels.pack import LevelPack, discover_pack
from git_tutorial.levels.scenario import LevelState
from git_tutorial.levels.setup_runner import run_setup
from git_tutorial.predicates.base import EvalContext
from git_tutorial.scene.warehouse import unreachable
from git_tutorial.session import hints as hint_rules
from git_tutorial.session import transitions
from git_tutorial.session.clock import Clock, SystemClock
from git_tutorial.state.models import LevelProgress, Progress
from git_tutorial.state.store import StateStore
from git_tutorial.testing.builder import RepoBuilder


class NoCurrentLevel(TutorialError):
    pass


class NotComplete(TutorialError):
    pass


def _env_answers() -> dict[str, str]:
    """GITTUTORIAL_ANSWERS=id=value,id=value — for CI, never for players."""
    raw = os.environ.get("GITTUTORIAL_ANSWERS", "")
    out: dict[str, str] = {}
    for pair in raw.split(","):
        key, sep, value = pair.partition("=")
        if sep:
            out[key.strip()] = value.strip()
    return out


Phase = Literal["working", "complete", "finished"]

# Kept in LevelProgress.extra: commits the yard should not draw for this job.
YARD_HIDDEN = "yard_hidden"


@dataclass(frozen=True, slots=True)
class CheckOutcome:
    report: CheckReport
    transitions: tuple[transitions.Transition, ...]
    # True on the one check that finished the level. Advancing is a separate
    # step the student asks for (`begin_next`): the next level's setup
    # rewrites the repository, and it must never do so mid-command.
    completed: bool = False
    finished: bool = False


def _worktree_paths(specs: tuple[AssertionSpec, ...]) -> list[str]:
    """Paths any worktree_unchanged assertion names, recursing into composites.

    Deriving the baseline from the assertions rather than trusting the setup
    script to call snapshot_worktree means a script that forgets the call can
    no longer produce an unguardable level.
    """
    found: list[str] = []

    def walk(items: tuple[AssertionSpec, ...]) -> None:
        for spec in items:
            if spec.kind == "worktree_unchanged":
                found.extend(str(p) for p in spec.args.get("paths", []))
            nested = spec.args.get("assert")
            if isinstance(nested, list):
                walk(tuple(
                    AssertionSpec(kind=str(n["kind"]),
                                  args={k: v for k, v in n.items() if k != "kind"})
                    for n in nested if isinstance(n, Mapping) and "kind" in n
                ))

    walk(specs)
    return found


class Session:
    """Owns level lifecycle. Never prints — CLI verbs render."""

    def __init__(
        self,
        *,
        worktree: Path,
        probe: GitRepoProbe,
        repo: RepoBuilder,
        pack: LevelPack,
        store: StateStore,
        clock: Clock | None = None,
    ) -> None:
        self.worktree = worktree
        self.probe = probe
        self.repo = repo
        self.pack = pack
        self.store = store
        self.clock = clock or SystemClock()
        # Kept from the last evaluate() so the browser's picture is drawn from
        # the very snapshot that was graded, without a second snapshot.
        self.last_snapshot: RepoSnapshot | None = None

    @classmethod
    def open(
        cls,
        *,
        repo_path: Path | None = None,
        levels: str | Path | None = None,
        clock: Clock | None = None,
    ) -> Session:
        probe = GitRepoProbe(repo_path or Path.cwd())
        worktree = probe.location.worktree
        return cls(
            worktree=worktree,
            probe=probe,
            repo=RepoBuilder(worktree, deterministic=False),
            pack=discover_pack(levels),
            store=StateStore(worktree),
            clock=clock,
        )

    # -- state ---------------------------------------------------------------

    @property
    def progress(self) -> Progress:
        return self.store.load()

    def phase(self, progress: Progress | None = None) -> Phase:
        progress = progress or self.progress
        if progress.finished:
            return "finished"
        current = progress.current()
        return "complete" if current is not None and current.completed else "working"

    def current_level(self, progress: Progress | None = None) -> Level:
        progress = progress or self.progress
        if progress.current_level_id is None:
            raise NoCurrentLevel("there is no level in progress")
        return self.pack.load(progress.current_level_id)

    def evaluate(
        self,
        *,
        progress: Progress | None = None,
        extra_answers: Mapping[str, str] | None = None,
    ) -> CheckReport:
        progress = progress or self.progress
        level = self.current_level(progress)
        entry = progress.for_level(level.id)
        answers = self.merged_answers(level, entry, extra_answers)

        snapshot = self.probe.snapshot()
        self.last_snapshot = snapshot
        with self.probe.blobs() as blobs:
            ctx = EvalContext(
                snapshot=snapshot,
                blobs=blobs,
                events=self.probe.events(),
                level_start_sha=entry.start_head or None,
                level_start_offsets=entry.start_offsets,
                level_start_worktree=entry.start_worktree,
                technique=level.technique,
                answers=answers,
            )
            return Checker.evaluate(level, ctx)

    # -- lifecycle -----------------------------------------------------------

    def begin_level(self, level_id: str, *, run_level_setup: bool = True) -> LevelProgress:
        level = self.pack.load(level_id)

        with self.store.mutate() as progress:
            entry = progress.for_level(level_id)
            if entry.completed_at is not None:
                entry.attempt += 1
                entry.completed_at = None

            # Commits that exist before setup and are unreachable after it are
            # the student's own work from earlier jobs, which setup has wound
            # back. Commits Head Office holds are not lost either: setup made
            # them as a colleague and sent them up. Both are hidden from the
            # yard, which is for what this job loses.
            existed = set(self.probe.snapshot().graph.nodes)

            if run_level_setup and level.setup:
                state = LevelState(
                    level_id=level_id,
                    start_time=self.clock.now(),
                    attempt=entry.attempt,
                    solved_before=level_id in progress.completed,
                    hints_shown=list(entry.hints_shown),
                    reset_count=entry.reset_count,
                )
                run_setup(level, self.repo, state, pack_root=self.pack.root)
                extra = state.extra_worktree_paths
            else:
                extra = []

            # Snapshot AFTER setup: @start must mean "the state the level
            # handed me", not the state before the level fabricated anything.
            snapshot = self.probe.snapshot()
            kept = existed | supplier.remote_commits(self.probe.runner)
            lost = set(unreachable(snapshot))
            # Colleagues' commits that setup made here and wound back, which
            # only origin/* names still reach: a later prune strands them,
            # but they were never this student's to lose either.
            local: set[str] = set()
            tips = [*snapshot.branches.values(), *snapshot.tags.values(), snapshot.head_sha]
            for tip in tips:
                if tip in snapshot.graph and tip not in local:
                    local.update(snapshot.graph.ancestors(tip))
            remote_only = set(snapshot.graph.nodes) - existed - local - lost
            entry.extra[YARD_HIDDEN] = sorted((lost & kept) | remote_only)
            entry.start_head = snapshot.head_sha
            entry.started_at = self.clock.now()
            # Where the reflogs end now. Everything after this mark is the
            # student's own work on this level - setup's own commits, resets
            # and branch deletions are all behind it, and a `used_command`
            # assertion must not be able to pass on the setup's typing.
            entry.start_offsets = self.probe.reflog_offsets()

            wanted = _worktree_paths(level.assertions) + extra
            entry.start_worktree = {
                path: sha
                for path in dict.fromkeys(wanted)
                if (sha := snapshot.worktree_blobs.get(path) or snapshot.index_blobs.get(path))
            }

            progress.current_level_id = level_id
            progress.finished_at = None
            progress.add_recap(self.clock.now(), f"You reached {level.title}.")

            report = self._evaluate_with(level, entry, snapshot)
            entry.last_results = transitions.to_snapshots(report)
            return entry

    def merged_answers(
        self,
        level: Level,
        entry: LevelProgress,
        extra: Mapping[str, str] | None = None,
    ) -> dict[str, str]:
        """Lowest to highest: what the student typed, then CI, then explicit."""
        merged = dict(entry.answers)
        merged.update(_env_answers())
        if extra:
            merged.update(extra)
        return merged

    def answer_slots(self, level: Level) -> dict[str, AnswerSlot]:
        return {slot.id: slot for slot in slots_for(level)}

    def _evaluate_with(
        self, level: Level, entry: LevelProgress, snapshot: object
    ) -> CheckReport:
        with self.probe.blobs() as blobs:
            ctx = EvalContext(
                snapshot=snapshot,  # type: ignore[arg-type]
                blobs=blobs,
                events=self.probe.events(),
                level_start_sha=entry.start_head or None,
                level_start_offsets=entry.start_offsets,
                level_start_worktree=entry.start_worktree,
                technique=level.technique,
                answers=self.merged_answers(level, entry),
            )
            return Checker.evaluate(level, ctx)

    def check(self, *, extra_answers: Mapping[str, str] | None = None) -> CheckOutcome:
        progress = self.progress
        level = self.current_level(progress)
        entry = progress.for_level(level.id)

        report = self.evaluate(progress=progress, extra_answers=extra_answers)
        happened = transitions.diff(entry.last_results, report)

        with self.store.mutate() as fresh:
            fresh.for_level(level.id).last_results = transitions.to_snapshots(report)

        # A finished level stays finished: undoing the work afterwards (as
        # Act 3 invites) must not take the student's tick away.
        if entry.completed or not report.complete or report.has_authoring_error:
            return CheckOutcome(report=report, transitions=happened)

        finished = self.complete_current()
        return CheckOutcome(report=report, transitions=happened, completed=True,
                            finished=finished)

    def complete_current(self) -> bool:
        """Mark the current level done. True when it was the last one.

        Does not advance: the student starts the next job when they are
        ready, and only then does its setup touch the repository.
        """
        progress = self.progress
        level = self.current_level(progress)
        last = self.pack.next_level_id(level.id) is None

        with self.store.mutate() as fresh:
            if fresh.current_level_id != level.id:
                return fresh.finished
            entry = fresh.for_level(level.id)
            if entry.completed_at is not None:
                return fresh.finished
            entry.completed_at = self.clock.now()
            # The end of this level is only readable now, before the next
            # level's setup adds its own reflog lines.
            entry.end_offsets = self.probe.reflog_offsets()
            entry.deeds = reflog.count_ops(
                reflog.since_offsets(self.probe.events(), entry.start_offsets)
            )
            if level.id not in fresh.completed:
                fresh.completed.append(level.id)
            fresh.add_recap(self.clock.now(), f"You finished {level.title}.")
            if last:
                fresh.finished_at = self.clock.now()
        return last

    def begin_next(self) -> str | None:
        """Start the level after the completed current one. None at the end."""
        progress = self.progress
        level = self.current_level(progress)
        if not progress.for_level(level.id).completed:
            raise NotComplete(f"{level.title} is not complete yet")
        next_id = self.pack.next_level_id(level.id)
        if next_id is None:
            return None
        self.begin_level(next_id)
        return next_id

    def reset_current(self) -> Level:
        progress = self.progress
        level = self.current_level(progress)
        with self.store.mutate() as fresh:
            fresh.for_level(level.id).reset_count += 1
        # Keeps hints_shown and answers: a reset is not a fresh brain.
        self.begin_level(level.id)
        return level

    def idle_seconds(self) -> float:
        """How long the student has been silent, by the reflog (spec 7.1).

        Measured from the newest event this level opened its window on, or
        from the level's own start if they have not moved anything yet. It
        reads what git recorded rather than wall-clock time at the terminal,
        so a window left open overnight does not count as a student stuck.

        It only sees commands that moved something. `status`, `log` and
        `diff` write no reflog line, so a student reading carefully looks
        idle here - which is why the loop takes the repository's own activity
        into account as well before it pushes anything.
        """
        progress = self.progress
        try:
            level = self.current_level(progress)
        except NoCurrentLevel:
            return 0.0

        entry = progress.for_level(level.id)
        window = reflog.since_offsets(self.probe.events(), entry.start_offsets)
        last = reflog.last_activity(window)
        return max(0.0, self.clock.now() - (last if last is not None else entry.started_at))

    def due_hint(self, idle_seconds: float) -> tuple[int, str] | None:
        """The rung the ladder has reached, shown once and recorded."""
        progress = self.progress
        try:
            level = self.current_level(progress)
        except NoCurrentLevel:
            return None

        entry = progress.for_level(level.id)
        index = hint_rules.due_now(
            level,
            entry.hints_shown,
            entry.hints_shown_at,
            idle_seconds=idle_seconds,
            now=self.clock.now(),
        )
        return None if index is None else self.show_hint(index)

    def show_hint(self, index: int | None = None) -> tuple[int, str] | None:
        progress = self.progress
        level = self.current_level(progress)
        entry = progress.for_level(level.id)

        chosen = index if index is not None else hint_rules.next_unshown(level, entry.hints_shown)
        if chosen is None or chosen >= len(level.hints):
            return None

        with self.store.mutate() as fresh:
            target = fresh.for_level(level.id)
            if chosen not in target.hints_shown:
                target.hints_shown.append(chosen)
                target.hints_shown_at.append(self.clock.now())
        return (chosen, level.hints[chosen].text)

    def record_answer(self, key: str, value: str) -> None:
        progress = self.progress
        level = self.current_level(progress)
        with self.store.mutate() as fresh:
            fresh.for_level(level.id).answers[key] = value

    def mark_solve_used(self) -> None:
        progress = self.progress
        level = self.current_level(progress)
        with self.store.mutate() as fresh:
            fresh.for_level(level.id).solve_used = True

    def recap(self, limit: int = 3) -> tuple[str, ...]:
        return self.progress.recent_recap(limit)
