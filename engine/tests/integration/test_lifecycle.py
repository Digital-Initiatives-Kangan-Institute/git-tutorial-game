from __future__ import annotations

from pathlib import Path

import pytest

from git_tutorial.levels.pack import discover_pack
from git_tutorial.levels.scenario import LevelState
from git_tutorial.levels.setup_runner import LevelSetupError, run_setup
from git_tutorial.session.lifecycle import Session
from git_tutorial.state.store import StateStore
from tests.conftest import write_level

pytestmark = pytest.mark.integration




class TestBeginLevel:
    def test_start_head_is_recorded_after_setup_runs(self, session: Session) -> None:
        """Named for the bug it prevents.

        If @start were captured before setup, `trees_equal @start WORKTREE`
        would compare against the pre-disaster commit — silently wrong, and
        invisible until Act 3.
        """
        session.repo.write("extra.txt", "x\n").commit("moved on")
        expected = session.repo.git("rev-parse", "HEAD").stdout.strip()

        entry = session.begin_level("level-1")
        assert entry.start_head == expected

    def test_setup_actually_ran(self, session: Session) -> None:
        session.begin_level("level-1")
        assert (session.worktree / "target.txt").exists()

    def test_last_results_are_stored_so_completion_is_a_transition(
        self, session: Session
    ) -> None:
        entry = session.begin_level("level-1")
        assert entry.last_results, "a level must record its opening state"
        assert not entry.last_results[0].passed


class TestWorktreeBaseline:
    def test_derived_from_the_assertions_without_the_setup_asking(
        self, tmp_path: Path, pack_root: Path, session: Session
    ) -> None:
        """A setup that forgets snapshot_worktree must not produce an
        unguardable level."""
        write_level(
            pack_root / "levels" / "level-1",
            "level-1",
            number=1,
            setup_body="""
                def setup(repo, state):
                    repo.write_file("guarded.txt", "original\\n")
                    repo.git("add", "guarded.txt")
                    repo.git("-c", "user.email=a@b", "-c", "user.name=a",
                             "commit", "-m", "guarded")
            """,
            assertions=(
                "- {kind: worktree_unchanged, paths: [guarded.txt]}\n"
                "- {kind: branch_exists, name: rescue}\n"
            ),
        )
        session.pack = discover_pack(pack_root)
        entry = session.begin_level("level-1")
        assert "guarded.txt" in entry.start_worktree


class TestProgression:
    def _solve_level_one(self, session: Session) -> None:
        session.repo.git("branch", "rescue")

    def test_completion_is_recorded_but_does_not_advance(self, session: Session) -> None:
        """The next job's setup rewrites the repo, so it waits to be asked."""
        session.begin_level("level-1")
        assert not session.check().completed
        assert session.phase() == "working"

        self._solve_level_one(session)
        outcome = session.check()

        assert outcome.report.complete and outcome.completed
        assert session.progress.completed == ["level-1"]
        assert session.progress.current_level_id == "level-1"
        assert session.phase() == "complete"

    def test_begin_next_advances_only_when_complete(self, session: Session) -> None:
        from git_tutorial.session.lifecycle import NotComplete

        session.begin_level("level-1")
        with pytest.raises(NotComplete):
            session.begin_next()

        self._solve_level_one(session)
        session.check()
        assert session.begin_next() == "level-2"
        assert session.progress.current_level_id == "level-2"
        assert session.phase() == "working"

    def test_a_completed_level_stays_completed(self, session: Session) -> None:
        """Act 3 invites undoing work; that must not take the tick away."""
        session.begin_level("level-1")
        self._solve_level_one(session)
        session.check()
        session.repo.git("branch", "-D", "rescue")
        assert not session.check().completed
        assert session.phase() == "complete"

    def test_completing_the_last_level_finishes_the_course(self, session: Session) -> None:
        session.begin_level("level-2")
        session.repo.git("branch", "second")
        outcome = session.check()

        assert outcome.finished
        assert session.phase() == "finished"
        assert session.progress.finished_at is not None
        assert session.begin_next() is None

    def test_complete_current_refuses_while_assertions_fail(self, session: Session) -> None:
        session.begin_level("level-1")
        session.check()
        assert session.progress.completed == []


class TestResetAndHints:
    def test_reset_reruns_setup_and_keeps_hints(self, session: Session) -> None:
        session.begin_level("level-1")
        session.show_hint()
        (session.worktree / "target.txt").unlink()

        session.reset_current()
        entry = session.progress.for_level("level-1")

        assert (session.worktree / "target.txt").exists()
        assert entry.reset_count == 1
        assert entry.hints_shown == [0], "a reset is not a fresh brain"

    def test_hints_come_in_order_then_run_out(self, session: Session) -> None:
        session.begin_level("level-1")
        assert session.show_hint() == (0, "first nudge")
        assert session.show_hint() == (1, "second nudge")
        assert session.show_hint() is None

    def test_a_fresh_session_does_not_refire_rung_zero(self, session: Session) -> None:
        session.begin_level("level-1")
        session.show_hint()

        reopened = Session(
            worktree=session.worktree, probe=session.probe, repo=session.repo,
            pack=session.pack, store=StateStore(session.worktree),
        )
        assert reopened.show_hint() == (1, "second nudge")


class TestSetupRunner:
    def test_same_basename_levels_load_independently(self, session: Session) -> None:
        """Every level's script is called setup.py; unnamespaced they collide."""
        session.begin_level("level-1")
        session.begin_level("level-2")
        assert session.progress.current_level_id == "level-2"

    def test_a_raising_setup_names_the_level_and_the_script(
        self, pack_root: Path, session: Session
    ) -> None:
        write_level(
            pack_root / "levels" / "level-1", "level-1", number=1,
            setup_body="""
                def setup(repo, state):
                    raise ValueError("the level author made a mistake")
            """,
            assertions="- {kind: branch_exists, name: rescue}\n",
        )
        session.pack = discover_pack(pack_root)

        with pytest.raises(LevelSetupError) as caught:
            session.begin_level("level-1")

        assert caught.value.level_id == "level-1"
        assert "the level author made a mistake" in str(caught.value)

    def test_a_setup_without_the_function_is_an_authoring_error(
        self, pack_root: Path, session: Session
    ) -> None:
        directory = pack_root / "levels" / "level-1"
        (directory / "setup.py").write_text("x = 1\n", encoding="utf-8")
        session.pack = discover_pack(pack_root)

        with pytest.raises(LevelSetupError, match="defines no setup"):
            session.begin_level("level-1")

    def test_a_pack_level_helper_is_importable(
        self, pack_root: Path, session: Session
    ) -> None:
        """A pip-installed pack and a git clone must behave identically."""
        (pack_root / "helpers.py").write_text("MARKER = 'from helpers'\n", encoding="utf-8")
        write_level(
            pack_root / "levels" / "level-1", "level-1", number=1,
            setup_body="""
                from helpers import MARKER

                def setup(repo, state):
                    repo.write_file("helper.txt", MARKER)
            """,
            assertions="- {kind: branch_exists, name: rescue}\n",
        )
        session.pack = discover_pack(pack_root)
        session.begin_level("level-1")

        assert (session.worktree / "helper.txt").read_text() == "from helpers"

    def test_run_setup_is_reusable_outside_a_session(
        self, pack_root: Path, session: Session
    ) -> None:
        level = discover_pack(pack_root).load("level-1")
        run_setup(level, session.repo, LevelState(level_id="level-1"), pack_root=pack_root)
        assert (session.worktree / "target.txt").exists()
