from __future__ import annotations

from collections.abc import Collection, Sequence

from git_tutorial.levels.model import Level


def next_unshown(level: Level, shown: Collection[int]) -> int | None:
    for index in range(len(level.hints)):
        if index not in shown:
            return index
    return None


def due_by_idle(level: Level, shown: Collection[int], idle_seconds: float) -> int | None:
    """The highest rung whose idle threshold has elapsed and which is unshown.

    What the ladder would have reached by now. `due_now` is what the loop
    actually pushes, because arriving at a rung and being handed it along
    with every rung below it are not the same thing.
    """
    due: int | None = None
    for index, hint in enumerate(level.hints):
        if index in shown:
            continue
        if idle_seconds >= hint.after_idle:
            due = index
        else:
            break
    return due


def due_now(
    level: Level,
    shown: Collection[int],
    shown_at: Sequence[float],
    *,
    idle_seconds: float,
    now: float,
) -> int | None:
    """The one rung to push, if any.

    One at a time and in order, because the lower rungs are the ones that
    teach - a student who stepped away for twenty minutes should not come
    back to the whole answer sitting on their screen. A rung becomes due
    after its own idle threshold, and then after the gap its author left
    between it and the rung before, so the escalation keeps the pace it was
    written with however long the silence ran.

    `shown_at` includes hints the student asked for with the Hint button, so asking
    for one also buys the quiet the author intended after it.
    """
    index = next_unshown(level, shown)
    if index is None:
        return None

    hint = level.hints[index]
    if idle_seconds < hint.after_idle:
        return None

    if shown_at:
        previous = level.hints[index - 1].after_idle if index else 0.0
        if now - max(shown_at) < hint.after_idle - previous:
            return None
    return index
