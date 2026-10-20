from __future__ import annotations

from pathlib import Path

import pytest

from git_tutorial.levels.model import HintSpec, Level
from git_tutorial.session.hints import due_now, next_unshown

pytestmark = pytest.mark.unit

NOW = 1_700_000_000.0


def level() -> Level:
    return Level(
        id="x", act=3, level=2, title="The Wake", directory=Path("."),
        hints=(
            HintSpec(after_idle=180, text="a question"),
            HintSpec(after_idle=420, text="the command"),
            HintSpec(after_idle=900, text="all of it"),
        ),
    )


class TestTheLadder:
    def test_silence_below_the_first_threshold_offers_nothing(self) -> None:
        assert due_now(level(), [], [], idle_seconds=179, now=NOW) is None
        assert due_now(level(), [], [], idle_seconds=180, now=NOW) == 0

    def test_a_long_silence_still_starts_at_the_bottom(self) -> None:
        """A student who stepped away for an hour should not come back to the
        whole answer; the lower rungs are the ones that teach."""
        assert due_now(level(), [], [], idle_seconds=3600, now=NOW) == 0

    def test_the_next_rung_waits_for_the_gap_its_author_left(self) -> None:
        shown, at = [0], [NOW]
        # 420 - 180: the pace the ladder was written with.
        assert due_now(level(), shown, at, idle_seconds=3600, now=NOW + 239) is None
        assert due_now(level(), shown, at, idle_seconds=3600, now=NOW + 240) == 1

    def test_asking_for_a_hint_buys_the_quiet_after_it(self) -> None:
        """`wt hint` records the same way, so pulling rung one does not make
        rung two arrive a second later."""
        assert due_now(level(), [0], [NOW], idle_seconds=3600, now=NOW + 10) is None

    def test_activity_resets_the_offer(self) -> None:
        assert due_now(level(), [0], [NOW], idle_seconds=12, now=NOW + 1000) is None

    def test_nothing_is_left_once_every_rung_is_shown(self) -> None:
        assert next_unshown(level(), [0, 1, 2]) is None
        assert due_now(level(), [0, 1, 2], [NOW], idle_seconds=99_999, now=NOW) is None

    def test_a_level_with_no_hints_is_silent(self) -> None:
        bare = Level(id="x", act=1, level=1, title="X", directory=Path("."))
        assert due_now(bare, [], [], idle_seconds=99_999, now=NOW) is None
