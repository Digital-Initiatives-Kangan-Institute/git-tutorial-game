from __future__ import annotations

from pathlib import Path

import pytest

from git_tutorial.git import reflog

pytestmark = pytest.mark.unit

WHO = "Student <s@x> 1726900000 +1000"


def write_log(tmp_path: Path, *lines: str) -> Path:
    path = tmp_path / "logs" / "HEAD"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{line}\n" for line in lines), encoding="utf-8")
    return path


class TestParsing:
    @pytest.mark.parametrize(
        ("message", "op", "detail"),
        [
            ("commit: fix parser", "commit", "fix parser"),
            ("commit (initial): first", "commit (initial)", "first"),
            ("commit (amend): reworded", "commit (amend)", "reworded"),
            ("checkout: moving from main to rescue", "checkout", "moving from main to rescue"),
            ("reset: moving to HEAD~2", "reset", "moving to HEAD~2"),
            ("revert: Revert \"bad idea\"", "revert", 'Revert "bad idea"'),
            ("branch: Created from HEAD", "branch", "Created from HEAD"),
            # The argument is part of the prefix, so the operation is its
            # first word - the shape `merge`, `pull` and `clone` all take.
            ("merge feature: Merge made by the 'ort' strategy.", "merge",
             "Merge made by the 'ort' strategy."),
            ("pull origin main: Fast-forward", "pull", "Fast-forward"),
            ("rebase (finish): returning to refs/heads/main", "rebase (finish)",
             "returning to refs/heads/main"),
        ],
    )
    def test_the_operation_vocabulary(self, message: str, op: str, detail: str) -> None:
        line = f"{'a' * 40} {'b' * 40} {WHO}\t{message}"
        event = reflog.parse_line(line, ref="HEAD", offset=0)
        assert event is not None
        assert (event.op, event.detail) == (op, detail)

    def test_every_parsed_op_is_in_the_vocabulary(self) -> None:
        """A level can only name ops from OPS, so a parser that invented one
        would make an assertion that could never be written."""
        for message in ("commit: x", "checkout: x", "reset: x", "merge f: x",
                        "pull o m: x", "revert: x", "branch: x", "cherry-pick: x"):
            line = f"{'a' * 40} {'b' * 40} {WHO}\t{message}"
            event = reflog.parse_line(line, ref="HEAD", offset=0)
            assert event is not None and event.op in reflog.OPS, message

    def test_an_unreadable_line_is_skipped_not_raised(self) -> None:
        """A student who is already stuck must not also get a traceback."""
        assert reflog.parse_line("garbage", ref="HEAD", offset=0) is None
        assert reflog.parse_line("", ref="HEAD", offset=0) is None


class TestTailReading:
    def test_a_tail_read_returns_only_what_is_new(self, tmp_path: Path) -> None:
        path = write_log(tmp_path, f"{'a' * 40} {'b' * 40} {WHO}\tcommit: one")
        first, offset = reflog.read_log(path, ref="HEAD")
        assert [e.detail for e in first] == ["one"]

        with path.open("a", encoding="utf-8") as handle:
            handle.write(f"{'b' * 40} {'c' * 40} {WHO}\tcommit: two\n")

        second, _ = reflog.read_log(path, ref="HEAD", since=offset)
        assert [e.detail for e in second] == ["two"]

    def test_a_half_written_line_is_left_for_next_time(self, tmp_path: Path) -> None:
        """A tick can land midway through git's own append. Consuming half a
        line would move the offset past it, losing it for good."""
        path = write_log(tmp_path, f"{'a' * 40} {'b' * 40} {WHO}\tcommit: one")
        with path.open("a", encoding="utf-8") as handle:
            handle.write(f"{'b' * 40} {'c' * 40} {WHO}\tcommit: tw")

        events, offset = reflog.read_log(path, ref="HEAD")
        assert [e.detail for e in events] == ["one"]

        with path.open("a", encoding="utf-8") as handle:
            handle.write("o\n")
        rest, _ = reflog.read_log(path, ref="HEAD", since=offset)
        assert [e.detail for e in rest] == ["two"]

    def test_a_rewritten_log_restarts_rather_than_slicing(self, tmp_path: Path) -> None:
        """`wt reset` re-runs setup, which can leave the log shorter than the
        offset we stored. Slicing from there would land mid-line."""
        path = write_log(tmp_path, f"{'a' * 40} {'b' * 40} {WHO}\tcommit: one")
        events, _ = reflog.read_log(path, ref="HEAD", since=10_000)
        assert [e.detail for e in events] == ["one"]

    def test_a_missing_log_is_empty_not_an_error(self, tmp_path: Path) -> None:
        events, offset = reflog.read_log(tmp_path / "nope", ref="HEAD")
        assert events == () and offset == 0


class TestWindow:
    def test_offsets_mark_where_the_level_begins(self, tmp_path: Path) -> None:
        write_log(tmp_path, f"{'a' * 40} {'b' * 40} {WHO}\tcommit: setup did this")
        marks = reflog.offsets(tmp_path)

        with (tmp_path / "logs" / "HEAD").open("a", encoding="utf-8") as handle:
            handle.write(f"{'b' * 40} {'c' * 40} {WHO}\treset: moving to HEAD~1\n")

        events, _ = reflog.read_all(tmp_path)
        assert len(events) == 2
        window = reflog.since_offsets(events, marks)
        assert [e.op for e in window] == ["reset"]

    def test_a_ref_with_no_mark_is_all_window(self, tmp_path: Path) -> None:
        """A branch created during the level did not exist to have a mark."""
        path = tmp_path / "logs" / "refs" / "heads" / "rescue"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{'0' * 40} {'b' * 40} {WHO}\tbranch: Created from HEAD\n")

        events, _ = reflog.read_all(tmp_path)
        assert reflog.since_offsets(events, {"HEAD": 999}) == events

    def test_nested_branch_names_are_found(self, tmp_path: Path) -> None:
        path = tmp_path / "logs" / "refs" / "heads" / "fix" / "the-thing"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{'0' * 40} {'b' * 40} {WHO}\tbranch: Created from HEAD\n")

        assert dict(reflog.log_paths(tmp_path)).keys() == {"refs/heads/fix/the-thing"}

    def test_last_activity_is_the_newest_event(self, tmp_path: Path) -> None:
        write_log(
            tmp_path,
            f"{'a' * 40} {'b' * 40} Student <s@x> 1726900000 +1000\tcommit: one",
            f"{'b' * 40} {'c' * 40} Student <s@x> 1726900500 +1000\tcommit: two",
        )
        events, _ = reflog.read_all(tmp_path)
        assert reflog.last_activity(events) == 1726900500
        assert reflog.last_activity(()) is None


class TestRemoteTracking:
    def test_remote_tracking_logs_are_read(self, tmp_path: Path) -> None:
        """Fetching and pushing are recorded here and nowhere else, and 4.10
        asks a student to read this log to recover an overwritten commit."""
        path = tmp_path / "logs" / "refs" / "remotes" / "origin" / "main"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"{'a' * 40} {'b' * 40} {WHO}\tfetch origin: fast-forward\n"
            f"{'b' * 40} {'c' * 40} {WHO}\tupdate by push\n",
            encoding="utf-8",
        )

        events, _ = reflog.read_all(tmp_path)
        assert [(e.ref, e.op) for e in events] == [
            ("refs/remotes/origin/main", "fetch"),
            ("refs/remotes/origin/main", "update"),
        ]
