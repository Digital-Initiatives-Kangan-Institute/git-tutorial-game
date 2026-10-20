from __future__ import annotations

from pathlib import Path

import pytest

from git_tutorial.checker import Checker
from git_tutorial.errors import LevelAuthoringError, RefResolutionError
from git_tutorial.levels.loader import load_level, parse_duration
from git_tutorial.predicates import evaluate
from git_tutorial.predicates.base import EvalContext
from git_tutorial.predicates.resolve import RefNotYetPresent, resolve
from git_tutorial.testing.builder import RepoBuilder

pytestmark = pytest.mark.integration


def ctx_for(repo: RepoBuilder, **kwargs: object) -> EvalContext:
    return EvalContext(snapshot=repo.snapshot(), blobs=repo.probe().blobs(), **kwargs)  # type: ignore[arg-type]


class TestCommitRefResolution:
    def test_every_documented_form(self, linear_repo: RepoBuilder) -> None:
        linear_repo.tutorial_ref("aldren-seal", "HEAD~1")
        linear_repo.tag("v1", "HEAD")
        linear_repo.reset("HEAD~1", "mixed")  # writes ORIG_HEAD
        head = linear_repo.git("rev-parse", "HEAD").stdout.strip()
        ctx = ctx_for(linear_repo, level_start_sha=head)

        assert resolve(ctx, "main") == ctx.snapshot.branches["main"]
        assert resolve(ctx, "tutorial:aldren-seal") == ctx.snapshot.tutorial_refs["aldren-seal"]
        assert resolve(ctx, "v1") == ctx.snapshot.tags["v1"]
        assert resolve(ctx, "HEAD") == head
        assert resolve(ctx, "@start") == head
        assert resolve(ctx, "@level_start") == head
        assert resolve(ctx, "ORIG_HEAD") == ctx.snapshot.special_refs["ORIG_HEAD"]
        assert resolve(ctx, "HEAD~1") == ctx.snapshot.graph.require(head).parents[0]
        assert resolve(ctx, head[:8]) == head

    def test_tilde_walks_multiple_steps(self, linear_repo: RepoBuilder) -> None:
        ctx = ctx_for(linear_repo)
        once = resolve(ctx, "HEAD~1")
        assert resolve(ctx, "HEAD~2") == ctx.snapshot.graph.require(once).parents[0]

    def test_caret_selects_a_merge_parent(self, repo: RepoBuilder) -> None:
        repo.write("f.txt", "base\n").commit("base")
        repo.branch("side")
        repo.write("a.txt", "a\n").commit("main work")
        main_tip = repo.git("rev-parse", "HEAD").stdout.strip()
        repo.switch("side")
        repo.write("b.txt", "b\n").commit("side work")
        side_tip = repo.git("rev-parse", "HEAD").stdout.strip()
        repo.switch("main")
        repo.merge("side", ff=False, message="merge")

        ctx = ctx_for(repo)
        assert resolve(ctx, "main^1") == main_tip
        assert resolve(ctx, "main^2") == side_tip

    def test_a_missing_branch_is_not_an_authoring_error(self, linear_repo: RepoBuilder) -> None:
        """The level asks the student to create it; not having it yet is the
        normal opening state, not a broken level."""
        ctx = ctx_for(linear_repo)
        with pytest.raises(RefNotYetPresent):
            resolve(ctx, "rescue")

    def test_a_missing_quest_ref_is_an_authoring_error(self, linear_repo: RepoBuilder) -> None:
        ctx = ctx_for(linear_repo)
        with pytest.raises(RefResolutionError) as caught:
            resolve(ctx, "tutorial:nope")
        assert not isinstance(caught.value, RefNotYetPresent)

    def test_start_without_a_recorded_sha_is_an_authoring_error(
        self, linear_repo: RepoBuilder
    ) -> None:
        with pytest.raises(RefResolutionError):
            resolve(ctx_for(linear_repo), "@start")

    def test_content_sentinels_are_rejected_as_commits(self, linear_repo: RepoBuilder) -> None:
        with pytest.raises(RefResolutionError):
            resolve(ctx_for(linear_repo), "WORKTREE")

    def test_walking_past_the_root_is_an_error(self, linear_repo: RepoBuilder) -> None:
        with pytest.raises(RefResolutionError):
            resolve(ctx_for(linear_repo), "HEAD~99")


class TestMissingRefSurfacesAsUnfinishedWork:
    def test_reported_as_a_failed_assertion_not_a_level_error(
        self, linear_repo: RepoBuilder
    ) -> None:
        result = evaluate(
            "trees_equal", ctx_for(linear_repo), {"a": "rescue", "b": "main"}
        )
        assert result.error is None, "a branch the student must create is not a content bug"
        assert not result.passed
        assert "does not exist yet" in result.found

    def test_a_broken_quest_ref_is_still_a_level_error(self, linear_repo: RepoBuilder) -> None:
        result = evaluate(
            "trees_equal", ctx_for(linear_repo), {"a": "main", "b": "tutorial:nope"}
        )
        assert result.error is not None


class TestLoader:
    def _write(self, tmp_path: Path, body: str) -> Path:
        path = tmp_path / "level.yaml"
        path.write_text(body, encoding="utf-8")
        return path

    def test_loads_a_full_level(self, tmp_path: Path) -> None:
        path = self._write(
            tmp_path,
            """
id: act3-02-the-wake
act: 3
level: 2
title: The Wake
technique: loose
teaches: [reflog, "reset --hard"]
reuses: ["log --graph", "switch -c"]
estimated_minutes: 12
setup: setup.py
solution: solution.sh
prose:
  intro: prose/intro.md
  brief: prose/brief.md
  beats:
    - on_state: {kind: branch_exists, name: rescue}
      text: prose/beats/rescue-born.md
assert:
  - kind: branch_exists
    name: rescue
hints:
  - after_idle: 180s
    text: "Destroyed is not gone."
  - after_idle: 7m
    text: "`git reflog` lists every position HEAD has held."
""",
        )
        level = load_level(path)

        assert level.id == "act3-02-the-wake"
        assert level.label == "act 3 · level 2"
        assert level.teaches == ("reflog", "reset --hard")
        assert level.hints[0].after_idle == 180
        assert level.hints[1].after_idle == 420
        assert level.prose.beats[0].on_state.kind == "branch_exists"
        assert level.assertion_keys() == ["0:branch_exists"]

    def test_an_unknown_assertion_kind_fails_at_load_time(self, tmp_path: Path) -> None:
        path = self._write(
            tmp_path,
            "id: x\nact: 1\ntitle: X\nassert:\n  - kind: no_such_thing\n",
        )
        with pytest.raises(LevelAuthoringError, match="no_such_thing"):
            load_level(path)

    def test_a_typo_in_an_assertion_arg_fails_at_load_time(self, tmp_path: Path) -> None:
        """Content CI should catch this, never a student mid-session."""
        path = self._write(
            tmp_path,
            "id: x\nact: 1\ntitle: X\nassert:\n  - kind: branch_exists\n    nmae: rescue\n",
        )
        with pytest.raises(LevelAuthoringError):
            load_level(path)

    def test_hints_must_escalate(self, tmp_path: Path) -> None:
        path = self._write(
            tmp_path,
            "id: x\nact: 1\ntitle: X\nhints:\n"
            "  - {after_idle: 400s, text: a}\n  - {after_idle: 200s, text: b}\n",
        )
        with pytest.raises(LevelAuthoringError, match="increase"):
            load_level(path)

    def test_bad_technique_is_rejected(self, tmp_path: Path) -> None:
        path = self._write(tmp_path, "id: x\nact: 1\ntitle: X\ntechnique: sorta\n")
        with pytest.raises(LevelAuthoringError, match="technique"):
            load_level(path)

    @pytest.mark.parametrize(
        ("text", "seconds"), [("180s", 180), ("7m", 420), ("1h", 3600), ("900", 900)]
    )
    def test_duration_forms(self, text: str, seconds: int) -> None:
        assert parse_duration(text) == seconds


class TestCheckerCompletion:
    def _level(self, tmp_path: Path, body: str) -> Path:
        path = tmp_path / "level.yaml"
        path.write_text(body, encoding="utf-8")
        return path

    @staticmethod
    def _merged_repo(repo: RepoBuilder) -> str:
        """A real diamond. Merging an ancestor is a no-op, so the two sides
        must genuinely diverge for a merge commit to exist."""
        repo.write("f.txt", "base\n").commit("base")
        base = repo.git("rev-parse", "HEAD").stdout.strip()
        repo.branch("side")
        repo.write("a.txt", "a\n").commit("main work")
        repo.switch("side")
        repo.write("b.txt", "b\n").commit("side work")
        repo.switch("main")
        repo.merge("side", ff=False, message="weave the timelines")
        return base

    def _body(self, technique: str, base: str) -> str:
        return (
            f"id: x\nact: 1\ntitle: X\ntechnique: {technique}\nassert:\n"
            "  - kind: head_on_branch\n    name: main\n"
            f"  - kind: graph_linear\n    from: {base}\n    to: main\n"
        )

    def test_advisory_rows_do_not_hold_a_loose_level_open(
        self, tmp_path: Path, repo: RepoBuilder
    ) -> None:
        """graph_linear is technique-gated: under `loose` it is shown but does
        not block, which is what makes 3.2's used_command assert coherent."""
        base = self._merged_repo(repo)
        level = load_level(self._level(tmp_path, self._body("loose", base)))
        report = Checker.evaluate(level, ctx_for(repo))

        advisory = report.results[1]
        assert not advisory.passed, "the fixture must actually contain a merge"
        assert not advisory.enforced
        assert report.complete, "a loose level must not be blocked by a technique row"

    def test_strict_makes_the_same_row_blocking(
        self, tmp_path: Path, repo: RepoBuilder
    ) -> None:
        base = self._merged_repo(repo)
        level = load_level(self._level(tmp_path, self._body("strict", base)))
        report = Checker.evaluate(level, ctx_for(repo))

        assert not report.results[1].passed
        assert report.results[1].enforced
        assert not report.complete

    def test_an_authoring_error_is_reported_separately_from_failure(
        self, tmp_path: Path, linear_repo: RepoBuilder
    ) -> None:
        body = (
            "id: x\nact: 1\ntitle: X\nassert:\n"
            "  - kind: trees_equal\n    a: main\n    b: tutorial:missing\n"
        )
        level = load_level(self._level(tmp_path, body))
        report = Checker.evaluate(level, ctx_for(linear_repo))

        assert report.has_authoring_error
        assert not report.complete
