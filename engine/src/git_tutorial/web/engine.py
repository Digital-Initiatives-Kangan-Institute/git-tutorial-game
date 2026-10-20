"""The watcher: grades the workspace and keeps the browser's picture current.

One thread owns the session. It polls the repository, grades the current
job, works out what moved, escalates hints, and publishes one immutable
state dict per change. The HTTP threads never touch the session: a button
press becomes a command on a queue, the engine applies it on its next step,
and the handler waits for the result. That single owner is why answers,
hints and "start the next job" can never race a grading pass.
"""

from __future__ import annotations

import queue
import threading
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from git_tutorial.checker import CheckReport
from git_tutorial.errors import TutorialError
from git_tutorial.levels.model import Level
from git_tutorial.session.clock import Clock, SystemClock
from git_tutorial.session.lifecycle import NoCurrentLevel, NotComplete, Session
from git_tutorial.session.moves import MoveTracker
from git_tutorial.state.lock import StateLockTimeout
from git_tutorial.web import state as page_state

POLL_SECONDS = 0.75
FULL_EVERY = 5.0  # Head Office can change while the workspace does not
HINT_EVERY = 5.0
LONG_POLL_SECONDS = 20.0
EVENTS_KEPT = 20
MAX_ANSWER = 200


@dataclass
class Command:
    kind: str
    data: dict[str, Any]
    done: threading.Event = field(default_factory=threading.Event)
    result: dict[str, Any] = field(default_factory=dict)


class Engine:
    def __init__(self, session: Session, *, clock: Clock | None = None) -> None:
        self.session = session
        self.clock = clock or SystemClock()
        self.tracker = MoveTracker(session.probe)
        self.error: str | None = None

        self._commands: queue.Queue[Command] = queue.Queue()
        self._wake = threading.Event()
        self._changed = threading.Condition()
        self._state: dict[str, Any] = {"seq": 0}
        self._events: deque[dict[str, Any]] = deque(maxlen=EVENTS_KEPT)
        self._next_event = 1

        self._key: tuple[Any, ...] | None = None
        self._full_at = float("-inf")
        self._hint_at = float("-inf")
        self._last_activity = self.clock.monotonic()
        self._level_seen: str | None = None
        self._completed_seen: str | None = None

    # -- the HTTP side ---------------------------------------------------------

    @property
    def current(self) -> dict[str, Any]:
        with self._changed:
            return self._state

    def wait(self, since: int, timeout: float = LONG_POLL_SECONDS) -> dict[str, Any]:
        with self._changed:
            self._changed.wait_for(lambda: self._state["seq"] != since, timeout=timeout)
            return self._state

    def submit(self, kind: str, data: dict[str, Any], timeout: float = 30.0) -> dict[str, Any]:
        """Queue a command from another thread and wait for its result."""
        command = Command(kind, data)
        self._commands.put(command)
        self._wake.set()
        if not command.done.wait(timeout):
            return {"ok": False, "status": 503, "error": "the watcher is busy; try again"}
        return command.result

    # -- the engine side -------------------------------------------------------

    def run(self, stop: threading.Event) -> None:
        while not stop.is_set():
            self.step()
            self._wake.wait(POLL_SECONDS)
            self._wake.clear()

    def step(self) -> bool:
        """One pass: apply queued commands, then regrade if anything changed.

        Never raises. A bad pass is reported on the page and retried, because
        the student's terminal is still working and they need to know.
        """
        commands: list[Command] = []
        while True:
            try:
                commands.append(self._commands.get_nowait())
            except queue.Empty:
                break

        changed = False
        try:
            for command in commands:
                command.result = self._apply(command)
            changed = self._observe(force=bool(commands))
            self.error = None
        except StateLockTimeout:
            pass  # someone else is writing progress; the next pass will see it
        except Exception as exc:  # the page must say so, not go quiet
            self.error = str(exc) or exc.__class__.__name__
            changed = self._publish_error()
        finally:
            for command in commands:
                if not command.result:
                    command.result = {"ok": False, "status": 500, "error": self.error or "failed"}
                command.done.set()
        return changed

    def _apply(self, command: Command) -> dict[str, Any]:
        session = self.session
        data = command.data
        if command.kind == "ping":
            self._last_activity = self.clock.monotonic()
            return {"ok": True}

        try:
            level = session.current_level()
        except NoCurrentLevel:
            return {"ok": False, "status": 409, "error": "there is no job in progress"}
        if str(data.get("level", level.id)) != level.id:
            return {"ok": False, "status": 409, "error": "that job is no longer the current one"}

        if command.kind == "answer":
            key = str(data.get("id", ""))
            if key not in session.answer_slots(level):
                return {"ok": False, "status": 400, "error": f"this job has no question {key!r}"}
            session.record_answer(key, str(data.get("value", "")).strip()[:MAX_ANSWER])
            self._last_activity = self.clock.monotonic()
            return {"ok": True}

        if command.kind == "hint":
            shown = session.show_hint()
            if shown is None:
                return {"ok": False, "status": 409, "error": "there are no more hints"}
            self._event("hint", rung=shown[0] + 1, asked=True)
            return {"ok": True}

        if command.kind == "next":
            if session.phase() != "complete":
                return {"ok": False, "status": 409, "error": "finish this job first"}
            if session.probe.locked() is not None:
                return {"ok": False, "status": 409,
                        "error": "git is busy in your workspace; try again in a moment"}
            try:
                started = session.begin_next()
            except NotComplete as exc:
                return {"ok": False, "status": 409, "error": str(exc)}
            self._key = None
            return {"ok": True, "level": started}

        if command.kind == "reset":
            if session.probe.locked() is not None:
                return {"ok": False, "status": 409,
                        "error": "git is busy in your workspace; try again in a moment"}
            session.reset_current()
            self._key = None
            self._event("level_reset", level=level.id)
            return {"ok": True}

        return {"ok": False, "status": 404, "error": f"unknown command {command.kind!r}"}

    def _observe(self, *, force: bool) -> bool:
        session = self.session
        probe = session.probe
        if probe.locked() is not None:
            return False
        fingerprint = probe.fingerprint()
        if fingerprint is None:
            return False

        # Editing a file touches nothing under .git, so the fingerprint alone
        # would miss the student's very first move. One cheap status call
        # sees the working tree too.
        status = probe.runner.run(
            "status", "--porcelain=v2", "-z", "--untracked-files=all", check=False
        ).stdout
        key = (fingerprint.parts, status, self._progress_stamp())
        now = self.clock.monotonic()
        changed = False
        if key != self._key or force or now - self._full_at >= FULL_EVERY:
            if self._key is not None and key != self._key:
                self._last_activity = now
            self._full_at = now
            changed = self._evaluate()
            # Grading writes progress. Stamp after it, or our own write would
            # look like the student doing something on the next pass.
            self._key = (fingerprint.parts, status, self._progress_stamp())
        return self._maybe_hint() or changed

    def _evaluate(self) -> bool:
        session = self.session
        try:
            level: Level | None = session.current_level()
        except NoCurrentLevel:
            level = None

        report: CheckReport | None = None
        if level is not None:
            if level.id != self._level_seen:
                if self._level_seen is not None:
                    self._event("level_arrived", level=level.id)
                self._level_seen = level.id
            if session.phase() == "working":
                outcome = session.check()
                report = outcome.report
                for transition in outcome.transitions:
                    if transition.kind != "level_complete":
                        self._event(str(transition.kind), goal=transition.key)
            else:
                report = session.evaluate()
            # Announced on the phase, not on our own check: `wt solve` or
            # `wt check` in the terminal can finish a job from another process.
            phase = session.phase()
            if phase != "working" and self._completed_seen != level.id:
                self._event("level_complete", level=level.id, last=phase == "finished")
            self._completed_seen = level.id if phase != "working" else None

        snapshot = session.last_snapshot or session.probe.snapshot()
        if self.tracker.observe(snapshot, level.id if level else None) and self.tracker.move:
            self._event("move", command=self.tracker.move.command)

        return self._publish(level, report, snapshot)

    def _publish(self, level: Level | None, report: CheckReport | None, snapshot: Any) -> bool:
        seq = self._state["seq"]
        fresh = page_state.build(
            self.session, level=level, report=report, snapshot=snapshot,
            move=self.tracker.move, unseen=self.tracker.unseen, office=self.tracker.office,
            remembered=self._remembered(),
            events=list(self._events), seq=seq + 1, error=self.error,
        )
        if {**fresh, "seq": seq} == self._state:
            return False
        with self._changed:
            self._state = fresh
            self._changed.notify_all()
        return True

    def _remembered(self) -> frozenset[str]:
        """Every commit any surviving reflog names, for the yard."""
        events = self.session.probe.events()
        return frozenset({e.new_sha for e in events} | {e.old_sha for e in events})

    def _publish_error(self) -> bool:
        with self._changed:
            if self._state.get("error") == self.error:
                return False
            self._state = {**self._state, "seq": self._state["seq"] + 1, "error": self.error}
            self._changed.notify_all()
        return True

    def _maybe_hint(self) -> bool:
        """Escalate the ladder when the student has gone quiet.

        Idle is the shorter of two measures: what the reflog says (commands
        that moved something) and what this watcher saw change (staging and
        editing, which leave no reflog line). Either one means working.
        """
        now = self.clock.monotonic()
        if now - self._hint_at < HINT_EVERY:
            return False
        self._hint_at = now
        session = self.session
        try:
            if session.phase() != "working":
                return False
            idle = min(session.idle_seconds(), now - self._last_activity)
            shown = session.due_hint(idle)
        except (TutorialError, OSError, StateLockTimeout):
            return False
        if shown is None:
            return False
        self._event("hint", rung=shown[0] + 1, asked=False)
        self._key = None
        return self._evaluate()

    def _event(self, kind: str, **data: Any) -> None:
        self._events.append({"id": self._next_event, "kind": kind, **data})
        self._next_event += 1

    def _progress_stamp(self) -> int:
        try:
            return self.session.store.progress_path.stat().st_mtime_ns
        except OSError:
            return 0
