"""Moves are detected from real repos, the way the watch loop sees them:
two snapshots and the reflog lines written between them (spec §11.4)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from git_tutorial.git import reflog, supplier
from git_tutorial.scene import warehouse
from git_tutorial.scene.warehouse import Move
from git_tutorial.testing.builder import RepoBuilder

pytestmark = pytest.mark.integration


def moved(repo: RepoBuilder, action: Callable[[], object]) -> Move | None:
    git_dir = repo.probe().git_dir
    before = repo.snapshot()
    marks = reflog.offsets(git_dir)
    action()
    events, _ = reflog.read_all(git_dir, since=marks)
    return warehouse.detect_move(before, repo.snapshot(), events)


@pytest.fixture
def remote(tmp_path: Path, linear_repo: RepoBuilder) -> Path:
    bare = tmp_path / "origin.git"
    linear_repo.git("init", "--bare", "-b", "main", str(bare))
    linear_repo.git("remote", "add", "origin", str(bare))
    linear_repo.git("push", "-u", "origin", "main")
    return bare


@pytest.fixture
def colleague(tmp_path: Path, remote: Path, linear_repo: RepoBuilder) -> RepoBuilder:
    path = tmp_path / "colleague"
    linear_repo.git("clone", str(remote), str(path))
    return RepoBuilder(path, home=tmp_path / "home")


class TestLocalMoves:
    def test_add(self, linear_repo: RepoBuilder) -> None:
        linear_repo.write("new.md", "n\n")
        move = moved(linear_repo, lambda: linear_repo.add("new.md"))
        assert move == Move("git add", "working tree", "staging area", "new.md")

    def test_unstage(self, linear_repo: RepoBuilder) -> None:
        linear_repo.write("new.md", "n\n").add("new.md")
        move = moved(linear_repo, lambda: linear_repo.git("restore", "--staged", "new.md"))
        assert move is not None and move.command == "git restore --staged"

    def test_an_edit_is_shown_without_a_command(self, linear_repo: RepoBuilder) -> None:
        move = moved(linear_repo, lambda: linear_repo.write("chronicle/index.md", "edited\n"))
        assert move == Move("edited", "", "working tree", "chronicle/index.md")

    def test_commit(self, linear_repo: RepoBuilder) -> None:
        linear_repo.write("new.md", "n\n").add("new.md")
        move = moved(linear_repo, lambda: linear_repo.commit("add new"))
        assert move is not None
        assert (move.command, move.source, move.dest) == ("git commit", "staging area",
                                                          "branch main")

    def test_amend(self, linear_repo: RepoBuilder) -> None:
        move = moved(linear_repo, lambda: linear_repo.git("commit", "--amend", "-m", "again"))
        assert move is not None and move.command == "git commit --amend"

    def test_reset_puts_commits_in_the_yard(self, linear_repo: RepoBuilder) -> None:
        move = moved(linear_repo, lambda: linear_repo.reset_hard("HEAD~2"))
        assert move == Move("git reset", "branch main", "reflog only", "2 commits off the branch")
        assert warehouse.build_scene(linear_repo.snapshot()).yard == 2

    def test_switch(self, linear_repo: RepoBuilder) -> None:
        linear_repo.branch("feature")
        move = moved(linear_repo, lambda: linear_repo.switch("feature"))
        assert move == Move("git switch", "branch main", "branch feature", "HEAD moved")

    def test_stash(self, linear_repo: RepoBuilder) -> None:
        linear_repo.write("chronicle/index.md", "edited\n")
        move = moved(linear_repo, lambda: linear_repo.stash())
        assert move is not None and move.command == "git stash"

    def test_a_conflict_is_a_hold(self, linear_repo: RepoBuilder) -> None:
        linear_repo.switch("other", create=True)
        linear_repo.write("chronicle/index.md", "theirs\n").commit("theirs")
        linear_repo.switch("main")
        linear_repo.write("chronicle/index.md", "ours\n").commit("ours")
        move = moved(linear_repo, lambda: linear_repo.git("merge", "other", check=False))
        assert move is not None and move.dest == "paused"
        scene = warehouse.build_scene(linear_repo.snapshot())
        assert scene.hold == "merge"
        assert any(item.mark == "!" for item in scene.floor)


class TestSupplierMoves:
    def test_push(self, linear_repo: RepoBuilder, remote: Path) -> None:
        linear_repo.write("new.md", "n\n").commit("mine")
        move = moved(linear_repo, lambda: linear_repo.git("push"))
        assert move == Move("git push", "branch main", "origin/main", "1 commit sent")

    def test_fetch_then_pull(self, linear_repo: RepoBuilder, colleague: RepoBuilder) -> None:
        colleague.write("theirs.md", "t\n").commit("theirs")
        colleague.git("push")

        before = linear_repo.snapshot()
        assert supplier.unseen(linear_repo.probe().runner, before) == 1

        move = moved(linear_repo, lambda: linear_repo.git("fetch"))
        assert move is not None and move.command == "git fetch"
        after = linear_repo.snapshot()
        assert supplier.unseen(linear_repo.probe().runner, after) == 0
        assert warehouse.build_scene(after).behind == 1

        move = moved(linear_repo, lambda: linear_repo.git("merge", "--ff-only", "origin/main"))
        assert move is not None and move.dest == "branch main"

    def test_pull_in_one_step(self, linear_repo: RepoBuilder, colleague: RepoBuilder) -> None:
        colleague.write("theirs.md", "t\n").commit("theirs")
        colleague.git("push")
        move = moved(linear_repo, lambda: linear_repo.git("pull", "--ff-only"))
        assert move is not None
        assert (move.command, move.source, move.dest) == ("git pull", "origin/main",
                                                          "branch main")

    def test_no_remote_means_nothing_unseen(self, linear_repo: RepoBuilder) -> None:
        assert supplier.unseen(linear_repo.probe().runner, linear_repo.snapshot()) is None

    def test_reset_past_pushed_commits_is_not_the_yard(
        self, linear_repo: RepoBuilder, remote: Path
    ) -> None:
        """They are still on origin/main, so "reflog only" would be untrue."""
        move = moved(linear_repo, lambda: linear_repo.reset_hard("HEAD~1"))
        assert move is not None
        assert move.dest == "off the branch"
        assert warehouse.build_scene(linear_repo.snapshot()).yard == 0


def moved_with_office(repo: RepoBuilder, action: Callable[[], object]) -> Move | None:
    """As `moved`, but also comparing what Head Office held before and after."""
    runner = repo.probe().runner
    git_dir = repo.probe().git_dir
    before, office_before = repo.snapshot(), supplier.head_office(runner)
    marks = reflog.offsets(git_dir)
    action()
    events, _ = reflog.read_all(git_dir, since=marks)
    return warehouse.detect_move(before, repo.snapshot(), events,
                                 office=(office_before, supplier.head_office(runner)))


class TestTeamMoves:
    """Act 5: the moves that change Head Office, or only names."""

    def test_tag(self, linear_repo: RepoBuilder) -> None:
        move = moved(linear_repo, lambda: linear_repo.git("tag", "stocktake-march"))
        assert move is not None and move.command == "git tag"
        assert move.dest == "tag stocktake-march"

    def test_tag_delete(self, linear_repo: RepoBuilder) -> None:
        linear_repo.git("tag", "wrong")
        move = moved(linear_repo, lambda: linear_repo.git("tag", "-d", "wrong"))
        assert move is not None and move.command == "git tag -d"

    def test_branch_delete(self, linear_repo: RepoBuilder) -> None:
        linear_repo.branch("peak-rota")
        move = moved(linear_repo, lambda: linear_repo.git("branch", "-d", "peak-rota"))
        assert move is not None and move.command == "git branch -d"
        assert move.source == "branch peak-rota"

    def test_pushing_a_tag(self, linear_repo: RepoBuilder, remote: Path) -> None:
        linear_repo.git("tag", "stocktake-march")
        move = moved_with_office(
            linear_repo, lambda: linear_repo.git("push", "origin", "stocktake-march"))
        assert move == Move("git push", "tag stocktake-march", "origin",
                            f"the seal on {linear_repo.resolve('HEAD')[:7]} is at Head Office now")

    def test_deleting_a_branch_at_head_office(
        self, linear_repo: RepoBuilder, remote: Path
    ) -> None:
        linear_repo.git("push", "origin", "main:peak-rota")
        move = moved_with_office(
            linear_repo, lambda: linear_repo.git("push", "origin", "--delete", "peak-rota"))
        assert move is not None and move.command == "git push --delete"

    def test_pruning_a_branch_head_office_already_deleted(
        self, linear_repo: RepoBuilder, remote: Path, colleague: RepoBuilder
    ) -> None:
        linear_repo.git("push", "origin", "main:old-bay")
        linear_repo.git("fetch")
        colleague.git("push", "origin", "--delete", "old-bay")
        move = moved_with_office(linear_repo, lambda: linear_repo.git("fetch", "--prune"))
        assert move is not None and move.command == "git fetch --prune"
        assert move.source == "origin/old-bay"


class TestHeadOffice:
    def test_branches_and_peeled_tags(self, linear_repo: RepoBuilder, remote: Path) -> None:
        linear_repo.git("tag", "-a", "-m", "signed off", "stocktake-march")
        linear_repo.git("push", "origin", "stocktake-march")
        office = supplier.head_office(linear_repo.probe().runner)
        assert office is not None
        assert office.branches == {"main": linear_repo.resolve("HEAD")}
        assert office.tags == {"stocktake-march": linear_repo.resolve("HEAD")}

    def test_no_remote_means_unknown(self, linear_repo: RepoBuilder) -> None:
        assert supplier.head_office(linear_repo.probe().runner) is None


def conflicted_pull(repo: RepoBuilder, colleague: RepoBuilder, *, theirs_deletes: bool = False
                    ) -> None:
    """A real `git pull` that stops: both sides changed chronicle/index.md."""
    if theirs_deletes:
        colleague.git("rm", "-q", "chronicle/index.md")
        colleague.git("commit", "-qm", "retire the index")
    else:
        colleague.write("chronicle/index.md", "their index\n").commit("their index")
    colleague.git("push", "-q")
    repo.write("chronicle/index.md", "our index\n").commit("our index")
    repo.git("pull", "--no-rebase", "--no-edit", check=False)


class TestConflictMoves:
    def test_the_held_file_says_what_kind_of_dispute(
        self, linear_repo: RepoBuilder, colleague: RepoBuilder
    ) -> None:
        conflicted_pull(linear_repo, colleague)
        held = [i for i in warehouse.build_scene(linear_repo.snapshot()).floor if i.mark == "!"]
        assert [(i.path, i.detail) for i in held] == [("chronicle/index.md", "both changed")]

    def test_taking_their_side_whole(
        self, linear_repo: RepoBuilder, colleague: RepoBuilder
    ) -> None:
        conflicted_pull(linear_repo, colleague)
        move = moved(linear_repo, lambda: linear_repo.git(
            "restore", "--theirs", "chronicle/index.md"))
        assert move is not None and move.command == "git restore --theirs"

    def test_adding_settles_the_conflict(
        self, linear_repo: RepoBuilder, colleague: RepoBuilder
    ) -> None:
        conflicted_pull(linear_repo, colleague)
        linear_repo.write("chronicle/index.md", "agreed index\n")
        move = moved(linear_repo, lambda: linear_repo.add("chronicle/index.md"))
        assert move is not None and move.command == "git add"
        assert "settled" in move.detail

    def test_rm_settles_a_modify_delete(
        self, linear_repo: RepoBuilder, colleague: RepoBuilder
    ) -> None:
        conflicted_pull(linear_repo, colleague, theirs_deletes=True)
        held = [i for i in warehouse.build_scene(linear_repo.snapshot()).floor if i.mark == "!"]
        assert held[0].detail == "deleted by them"
        move = moved(linear_repo, lambda: linear_repo.git("rm", "-q", "chronicle/index.md"))
        assert move is not None and move.command == "git rm"

    def test_rm_of_an_ordinary_file(self, linear_repo: RepoBuilder) -> None:
        move = moved(linear_repo, lambda: linear_repo.git("rm", "-q", "chronicle/index.md"))
        assert move is not None and move.command == "git rm"

    def test_a_pull_that_stops_is_named_as_a_pull(
        self, linear_repo: RepoBuilder, colleague: RepoBuilder
    ) -> None:
        colleague.write("chronicle/index.md", "their index\n").commit("their index")
        colleague.git("push", "-q")
        linear_repo.write("chronicle/index.md", "our index\n").commit("our index")
        move = moved(linear_repo, lambda: linear_repo.git(
            "pull", "--no-rebase", "--no-edit", check=False))
        assert move is not None
        assert (move.command, move.dest) == ("git pull", "paused")
