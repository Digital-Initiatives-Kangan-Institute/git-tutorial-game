from __future__ import annotations

from collections.abc import Iterator

import pytest

from git_tutorial.errors import LevelAuthoringError
from git_tutorial.predicates import REGISTRY, evaluate
from git_tutorial.predicates.base import EvalContext
from git_tutorial.testing.builder import RepoBuilder

pytestmark = pytest.mark.integration


@pytest.fixture
def ctx(linear_repo: RepoBuilder) -> Iterator[EvalContext]:
    with linear_repo.probe().blobs() as blobs:
        yield EvalContext(snapshot=linear_repo.snapshot(), blobs=blobs)


def rebuild(repo: RepoBuilder, **kwargs: object) -> EvalContext:
    return EvalContext(snapshot=repo.snapshot(), blobs=repo.probe().blobs(), **kwargs)  # type: ignore[arg-type]


class TestHeadPredicates:
    def test_head_on_branch(self, ctx: EvalContext) -> None:
        ok = evaluate("head_on_branch", ctx, {"name": "main"})
        assert ok.passed and "main" in ok.found

        bad = evaluate("head_on_branch", ctx, {"name": "rescue"})
        assert not bad.passed

    def test_head_detached(self, linear_repo: RepoBuilder) -> None:
        assert not evaluate("head_detached", rebuild(linear_repo), {}).passed

        linear_repo.detach("HEAD~1")
        ctx = rebuild(linear_repo)
        assert evaluate("head_detached", ctx, {}).passed
        assert evaluate("head_detached", ctx, {"at": "main~1"}).passed
        assert not evaluate("head_detached", ctx, {"at": "main"}).passed


class TestBranchPredicates:
    def test_branch_exists_both_directions(self, linear_repo: RepoBuilder) -> None:
        ctx = rebuild(linear_repo)
        assert evaluate("branch_exists", ctx, {"name": "main"}).passed
        assert evaluate("branch_exists", ctx, {"name": "rescue", "exists": False}).passed
        assert not evaluate("branch_exists", ctx, {"name": "rescue"}).passed

    def test_branch_at(self, linear_repo: RepoBuilder) -> None:
        linear_repo.branch("rescue", "HEAD~1")
        ctx = rebuild(linear_repo)
        assert evaluate("branch_at", ctx, {"name": "rescue", "commit": "main~1"}).passed
        assert not evaluate("branch_at", ctx, {"name": "rescue", "commit": "main"}).passed


class TestGraphPredicates:
    def test_is_ancestor(self, ctx: EvalContext) -> None:
        assert evaluate("is_ancestor", ctx, {"ancestor": "HEAD~2", "descendant": "HEAD"}).passed
        assert not evaluate(
            "is_ancestor", ctx, {"ancestor": "HEAD", "descendant": "HEAD~2"}
        ).passed

    def test_parent_count_names_the_shape(self, repo: RepoBuilder) -> None:
        repo.write("f.txt", "base\n").commit("base")
        repo.branch("side")
        repo.write("a.txt", "a\n").commit("main work")
        repo.switch("side")
        repo.write("b.txt", "b\n").commit("side work")
        repo.switch("main")
        repo.merge("side", ff=False, message="weave the timelines")

        ctx = rebuild(repo)
        merge = evaluate("parent_count", ctx, {"of": "main", "count": 2})
        assert merge.passed
        assert "merge commit" in merge.want

        linear = evaluate("parent_count", ctx, {"of": "main^1", "count": 1})
        assert linear.passed

    def test_commit_count_uses_exclusion_semantics(self, ctx: EvalContext) -> None:
        assert evaluate("commit_count", ctx, {"from": "HEAD", "exactly": 3}).passed
        assert evaluate(
            "commit_count", ctx, {"from": "HEAD", "not_from": "HEAD~2", "exactly": 2}
        ).passed

    def test_graph_linear_spots_a_merge(self, repo: RepoBuilder) -> None:
        repo.write("f.txt", "base\n").commit("base")
        base = repo.git("rev-parse", "HEAD").stdout.strip()
        repo.branch("side")
        repo.write("a.txt", "a\n").commit("main work")
        repo.switch("side")
        repo.write("b.txt", "b\n").commit("side work")
        repo.switch("main")
        repo.merge("side", ff=False, message="merge")

        ctx = rebuild(repo, technique="strict")
        assert not evaluate("graph_linear", ctx, {"from": base, "to": "main"}).passed


class TestTreesAndContent:
    def test_trees_equal_ignores_the_route_taken(self, linear_repo: RepoBuilder) -> None:
        linear_repo.tutorial_ref("seal", "HEAD")
        linear_repo.branch("rescue", "HEAD")
        assert evaluate(
            "trees_equal", rebuild(linear_repo), {"a": "rescue", "b": "tutorial:seal"}
        ).passed

    def test_file_content_at_a_commit(self, ctx: EvalContext) -> None:
        ok = evaluate(
            "file_content", ctx, {"path": "chronicle/ledger.md", "at": "HEAD",
                                  "contains": "the second"}
        )
        assert ok.passed

        missing = evaluate(
            "file_content", ctx, {"path": "chronicle/ledger.md", "at": "HEAD~2",
                                  "contains": "the second"}
        )
        assert not missing.passed

    def test_file_content_reads_the_worktree(self, linear_repo: RepoBuilder) -> None:
        linear_repo.write("chronicle/ledger.md", "hand edited\n")
        ctx = rebuild(linear_repo)
        assert evaluate(
            "file_content", ctx, {"path": "chronicle/ledger.md", "contains": "hand edited"}
        ).passed

    def test_file_absent(self, ctx: EvalContext) -> None:
        assert evaluate("file_absent", ctx, {"path": "nope.md", "at": "HEAD"}).passed
        assert not evaluate(
            "file_absent", ctx, {"path": "chronicle/ledger.md", "at": "HEAD"}
        ).passed


class TestWorkingState:
    def test_status_clean(self, linear_repo: RepoBuilder) -> None:
        assert evaluate("status_clean", rebuild(linear_repo), {}).passed

        linear_repo.write("chronicle/ledger.md", "dirty\n")
        assert not evaluate("status_clean", rebuild(linear_repo), {}).passed

    def test_untracked_allowed_when_asked(self, linear_repo: RepoBuilder) -> None:
        linear_repo.write("scratch.txt", "notes\n")
        ctx = rebuild(linear_repo)
        assert not evaluate("status_clean", ctx, {}).passed
        assert evaluate("status_clean", ctx, {"allow_untracked": True}).passed

    def test_file_staged(self, linear_repo: RepoBuilder) -> None:
        linear_repo.write("chronicle/ledger.md", "staged edit\n").add()
        ctx = rebuild(linear_repo)
        assert evaluate("file_staged", ctx, {"path": "chronicle/ledger.md"}).passed
        assert not evaluate("file_staged", ctx, {"path": "chronicle/index.md"}).passed

    def test_stash_count(self, linear_repo: RepoBuilder) -> None:
        linear_repo.write("chronicle/ledger.md", "wip\n").stash()
        assert evaluate("stash_count", rebuild(linear_repo), {"exactly": 1}).passed

    def test_in_progress_merge(self, repo: RepoBuilder) -> None:
        repo.write("f.txt", "base\n").commit("base")
        repo.branch("other")
        repo.write("f.txt", "main\n").commit("main edit")
        repo.switch("other")
        repo.write("f.txt", "other\n").commit("other edit")
        repo.git("merge", "main", check=False)

        ctx = rebuild(repo)
        assert evaluate("in_progress", ctx, {"op": "MERGE_HEAD"}).passed
        assert not evaluate("in_progress", ctx, {"op": "MERGE_HEAD", "expected": False}).passed

    def test_worktree_unchanged_catches_hand_editing(self, linear_repo: RepoBuilder) -> None:
        path = "chronicle/ledger.md"
        baseline = dict(linear_repo.snapshot().index_blobs)

        assert evaluate(
            "worktree_unchanged",
            rebuild(linear_repo, level_start_worktree=baseline),
            {"paths": [path]},
        ).passed

        linear_repo.write(path, "retyped from memory\n")
        cheated = evaluate(
            "worktree_unchanged",
            rebuild(linear_repo, level_start_worktree=baseline),
            {"paths": [path]},
        )
        assert not cheated.passed
        assert "hand" in cheated.found


class TestAnswerPredicate:
    def test_answer_is_case_insensitive(self, ctx: EvalContext) -> None:
        answered = EvalContext(
            snapshot=ctx.snapshot, blobs=ctx.blobs, answers={"branch": "  MAIN "}
        )
        assert evaluate("answer", answered, {"id": "branch", "equals": "main"}).passed

    def test_unanswered_points_at_the_job_sheet(self, ctx: EvalContext) -> None:
        """It used to name a `wt answer` command that has never existed.
        answers.md is the only way in, and this is the most-seen line in the
        game: every unanswered question shows it."""
        result = evaluate("answer", ctx, {"id": "branch", "equals": "main"})
        assert not result.passed
        assert result.found == "not answered yet — type your answer on the job sheet"

    def test_surrounding_punctuation_is_forgiven(self, ctx: EvalContext) -> None:
        """Being told you are wrong when you are right loses people on level one."""
        for typed in ("`main`", '"main"', "main.", "  main  "):
            answered = EvalContext(snapshot=ctx.snapshot, blobs=ctx.blobs,
                                   answers={"branch": typed})
            assert evaluate("answer", answered, {"id": "branch", "equals": "main"}).passed

    def test_accepts_lists_alternatives(self, ctx: EvalContext) -> None:
        answered = EvalContext(snapshot=ctx.snapshot, blobs=ctx.blobs,
                               answers={"who": "Aldren Voss"})
        result = evaluate(
            "answer", answered, {"id": "who", "equals": "Aldren", "accepts": ["Aldren Voss"]}
        )
        assert result.passed

    def test_a_commit_answer_accepts_any_unambiguous_prefix(
        self, linear_repo: RepoBuilder
    ) -> None:
        """git itself accepts abbreviated hashes; so must the question."""
        target = linear_repo.git("rev-parse", "HEAD~1").stdout.strip()
        for typed in (target, target[:7], target[:10]):
            ctx = EvalContext(
                snapshot=linear_repo.snapshot(),
                blobs=linear_repo.probe().blobs(),
                answers={"h": typed},
            )
            result = evaluate("answer", ctx, {"id": "h", "equals_commit": "HEAD~1"})
            assert result.passed, f"{typed} should resolve to {target}"

    def test_a_commit_answer_rejects_a_different_commit(
        self, linear_repo: RepoBuilder
    ) -> None:
        ctx = EvalContext(
            snapshot=linear_repo.snapshot(),
            blobs=linear_repo.probe().blobs(),
            answers={"h": linear_repo.git("rev-parse", "HEAD").stdout.strip()},
        )
        assert not evaluate("answer", ctx, {"id": "h", "equals_commit": "HEAD~1"}).passed

    def test_a_commit_answer_that_is_not_a_commit_says_so(
        self, linear_repo: RepoBuilder
    ) -> None:
        ctx = EvalContext(
            snapshot=linear_repo.snapshot(),
            blobs=linear_repo.probe().blobs(),
            answers={"h": "not-a-hash"},
        )
        result = evaluate("answer", ctx, {"id": "h", "equals_commit": "HEAD"})
        assert not result.passed
        assert "does not name a commit" in result.found


class TestComposition:
    def test_all_of_and_any_of(self, ctx: EvalContext) -> None:
        good = {"kind": "head_on_branch", "name": "main"}
        bad = {"kind": "head_on_branch", "name": "rescue"}

        assert evaluate("all_of", ctx, {"assert": [good, good]}).passed
        assert not evaluate("all_of", ctx, {"assert": [good, bad]}).passed
        assert evaluate("any_of", ctx, {"assert": [good, bad]}).passed
        assert evaluate("not", ctx, {"assert": [bad]}).passed


class TestRegistryContract:
    def test_every_predicate_explains_itself_on_success(self, linear_repo: RepoBuilder) -> None:
        """Spec 6.3: want and found are populated even when an assertion passes."""
        linear_repo.tutorial_ref("seal", "HEAD")
        linear_repo.tag("v1")
        ctx = rebuild(linear_repo)

        passing: dict[str, dict[str, object]] = {
            "head_on_branch": {"name": "main"},
            "branch_exists": {"name": "main"},
            "branch_at": {"name": "main", "commit": "HEAD"},
            "is_ancestor": {"ancestor": "HEAD~1", "descendant": "HEAD"},
            "parent_count": {"of": "HEAD", "count": 1},
            "status_clean": {},
            "tag_exists": {"name": "v1"},
            "trees_equal": {"a": "HEAD", "b": "tutorial:seal"},
            "stash_count": {"exactly": 0},
            "commit_count": {"from": "HEAD", "exactly": 3},
            "in_progress": {"op": "MERGE_HEAD", "expected": False},
            "file_content": {"path": "chronicle/ledger.md", "at": "HEAD",
                             "contains": "the first"},
        }
        for kind, args in passing.items():
            result = evaluate(kind, ctx, args)
            assert result.passed, f"{kind} should pass: {result.found}"
            assert result.want, f"{kind} left `want` empty on success"
            assert result.found, f"{kind} left `found` empty on success"

    def test_unknown_kind_is_an_authoring_error_not_a_failure(self, ctx: EvalContext) -> None:
        result = evaluate("no_such_predicate", ctx, {})
        assert result.error is not None
        assert not result.passed

    def test_unknown_arg_is_rejected(self, ctx: EvalContext) -> None:
        result = evaluate("branch_exists", ctx, {"name": "main", "nmae": "typo"})
        assert result.error is not None and "nmae" in result.error

    def test_missing_required_arg_is_rejected(self, ctx: EvalContext) -> None:
        assert evaluate("branch_at", ctx, {"name": "main"}).error is not None

    def test_one_of_requires_exactly_one(self, ctx: EvalContext) -> None:
        both = evaluate(
            "file_content",
            ctx,
            {"path": "chronicle/ledger.md", "contains": "a", "matches": "b"},
        )
        assert both.error is not None

    def test_registry_covers_the_documented_set(self) -> None:
        expected = {
            "head_on_branch", "head_detached", "branch_exists", "branch_at", "is_ancestor",
            "commit_reachable", "parent_count", "file_content", "status_clean", "file_staged",
            "remote_ref_at", "answer", "tag_exists", "commit_count", "graph_linear",
            "trees_equal", "file_absent", "stash_count", "ahead_behind", "in_progress",
            "worktree_unchanged", "all_of", "any_of", "not",
        }
        assert expected <= set(REGISTRY), f"missing: {sorted(expected - set(REGISTRY))}"

    def test_args_spec_validation_raises_outside_evaluate(self) -> None:
        with pytest.raises(LevelAuthoringError):
            REGISTRY["branch_exists"].args.validate("branch_exists", {})


class TestConflictAndDivergence:
    """Act 2's shapes. Built with real git, because a conflict fabricated by
    hand is not the thing the student will be looking at."""

    @pytest.fixture
    def conflicted_repo(self, repo: RepoBuilder) -> RepoBuilder:
        repo.write("ledger.md", "base\n").commit("base")
        repo.branch("other")
        repo.write("ledger.md", "main says this\n").commit("main edit")
        repo.switch("other")
        repo.write("ledger.md", "other says this\n").commit("other edit")
        repo.git("merge", "main", check=False)
        return repo

    def test_conflicted_names_the_file(self, conflicted_repo: RepoBuilder) -> None:
        ctx = rebuild(conflicted_repo)
        assert evaluate("conflicted", ctx, {}).passed
        assert evaluate("conflicted", ctx, {"path": "ledger.md"}).passed
        assert not evaluate("conflicted", ctx, {"path": "nothing.md"}).passed

    def test_a_clean_repo_has_no_conflicts(self, linear_repo: RepoBuilder) -> None:
        ctx = rebuild(linear_repo)
        assert evaluate("conflicted", ctx, {"expected": False}).passed
        assert not evaluate("conflicted", ctx, {}).passed

    def test_a_conflicted_file_is_not_reported_as_staged(
        self, conflicted_repo: RepoBuilder
    ) -> None:
        """Its index status is U, which the staged test read as staged."""
        ctx = rebuild(conflicted_repo)
        result = evaluate("file_staged", ctx, {"path": "ledger.md", "staged": False})
        assert result.passed, result.found
        assert "conflicted" in result.found

    def test_ahead_behind_works_between_two_local_branches(
        self, repo: RepoBuilder
    ) -> None:
        """The Act 2 question - how far has the feature branch diverged -
        has no remote in it at all."""
        repo.write("a.md", "a\n").commit("base")
        repo.branch("feature")
        repo.write("b.md", "b\n").commit("main moves on")
        repo.switch("feature")
        repo.write("c.md", "c\n").commit("feature work")
        repo.write("d.md", "d\n").commit("more feature work")

        ctx = rebuild(repo)
        result = evaluate("ahead_behind", ctx,
                          {"branch": "feature", "upstream": "main", "ahead": 2, "behind": 1})
        assert result.passed, result.found


class TestInProgressIsNotSilentlyAlwaysTrue:
    def test_a_marker_that_does_not_exist_is_an_authoring_error(self) -> None:
        """`op: merge` instead of MERGE_HEAD is never present, so
        `expected: false` used to pass in every repository on earth."""
        with pytest.raises(LevelAuthoringError, match="merge"):
            REGISTRY["in_progress"].args.validate("in_progress", {"op": "merge", "expected": False})

    def test_the_real_markers_are_accepted(self) -> None:
        for op in ("MERGE_HEAD", "CHERRY_PICK_HEAD", "rebase-merge"):
            REGISTRY["in_progress"].args.validate("in_progress", {"op": op})


class TestTechniquePredicates:
    """The reflog is the only thing that can tell `reset` from `revert` once
    they have left the same tree behind (spec 6.5)."""

    def window(self, repo: RepoBuilder, marks: dict[str, int]) -> EvalContext:
        return rebuild(repo, events=repo.probe().events(), level_start_offsets=marks)

    def test_used_command_sees_what_the_student_typed(self, linear_repo: RepoBuilder) -> None:
        marks = linear_repo.probe().reflog_offsets()
        linear_repo.git("reset", "--hard", "HEAD~1")

        ctx = self.window(linear_repo, marks)
        used = evaluate("used_command", ctx, {"ops": ["reset"]})
        assert used.passed
        assert "moving to" in (used.detail or "")
        assert not evaluate("used_command", ctx, {"ops": ["revert"]}).passed

    def test_the_window_excludes_what_setup_did(self, linear_repo: RepoBuilder) -> None:
        """Setup commits, resets and deletes branches on the student's behalf.
        A level asserting `used_command: commit` must not pass on that."""
        marks = linear_repo.probe().reflog_offsets()
        ctx = self.window(linear_repo, marks)

        assert not evaluate("used_command", ctx, {"ops": ["commit"]}).passed

        linear_repo.write("chronicle/ledger.md", "mine\n").commit("my own work")
        assert evaluate("used_command", self.window(linear_repo, marks),
                        {"ops": ["commit"]}).passed

    def test_not_used_command_catches_the_wrong_route(self, linear_repo: RepoBuilder) -> None:
        """3.4 teaches `revert` precisely because `reset` would also leave the
        tree right."""
        marks = linear_repo.probe().reflog_offsets()
        linear_repo.git("reset", "--hard", "HEAD~1")

        failed = evaluate("not_used_command", self.window(linear_repo, marks),
                          {"ops": ["reset"]})
        assert not failed.passed
        assert "reset" in (failed.detail or "")

    def test_one_commit_counts_once(self, linear_repo: RepoBuilder) -> None:
        """A commit writes a line to logs/HEAD and to the branch's own log.
        Counting both would make `at_least: 2` pass on a single commit."""
        marks = linear_repo.probe().reflog_offsets()
        linear_repo.write("chronicle/ledger.md", "one\n").commit("one")

        ctx = self.window(linear_repo, marks)
        assert evaluate("used_command", ctx, {"ops": ["commit"], "at_least": 1}).passed
        assert not evaluate("used_command", ctx, {"ops": ["commit"], "at_least": 2}).passed

    def test_on_ref_reads_a_branch_log(self, linear_repo: RepoBuilder) -> None:
        marks = linear_repo.probe().reflog_offsets()
        linear_repo.switch("rescue", create=True)
        linear_repo.write("chronicle/ledger.md", "rescued\n").commit("on the branch")

        ctx = self.window(linear_repo, marks)
        assert evaluate("used_command", ctx,
                        {"ops": ["commit"], "on_ref": "rescue"}).passed
        assert not evaluate("used_command", ctx,
                            {"ops": ["commit"], "on_ref": "main"}).passed

    def test_switching_is_recorded_as_checkout(self, linear_repo: RepoBuilder) -> None:
        """`git switch` writes `checkout:` lines, so a level teaching switch
        asserts on checkout - and would silently never fire otherwise."""
        marks = linear_repo.probe().reflog_offsets()
        linear_repo.switch("rescue", create=True)

        assert evaluate("used_command", self.window(linear_repo, marks),
                        {"ops": ["checkout"]}).passed

    def test_they_are_advisory_under_loose_technique(self, linear_repo: RepoBuilder) -> None:
        """Shown, so the student learns what was noticed; not blocking, because
        only a level that declares `technique: strict` is grading the route."""
        marks = linear_repo.probe().reflog_offsets()
        loose = self.window(linear_repo, marks)
        result = evaluate("used_command", loose, {"ops": ["reset"]})
        assert not result.passed and not result.enforced and not result.blocking

        strict = EvalContext(
            snapshot=loose.snapshot, blobs=loose.blobs, events=loose.events,
            level_start_offsets=marks, technique="strict",
        )
        assert evaluate("used_command", strict, {"ops": ["reset"]}).blocking

    def test_an_op_outside_the_vocabulary_is_an_authoring_error(
        self, linear_repo: RepoBuilder
    ) -> None:
        """A typo here makes `used_command` unpassable and `not_used_command`
        true everywhere - the vacuous-green bug 7e13766 went hunting for."""
        ctx = rebuild(linear_repo)
        # Surfaced as an authoring error, never as a student failure (6.2),
        # and raised outright by the loader before a level can ship.
        typo = evaluate("used_command", ctx, {"ops": ["restore"]})
        assert typo.error is not None and "restore" in typo.error
        assert "empty" in (evaluate("not_used_command", ctx, {"ops": []}).error or "")
        assert "since" in (
            evaluate("used_command", ctx, {"ops": ["reset"], "since": "@forever"}).error or ""
        )

        with pytest.raises(LevelAuthoringError, match="restore"):
            REGISTRY["used_command"].args.validate("used_command", {"ops": ["restore"]})

    def test_a_list_arg_still_accepts_its_vocabulary(self, linear_repo: RepoBuilder) -> None:
        """The guard above must not be so keen that no level can use it."""
        marks = linear_repo.probe().reflog_offsets()
        linear_repo.git("reset", "--hard", "HEAD~1")
        assert evaluate(
            "used_command",
            self.window(linear_repo, marks),
            {"ops": ["reset", "revert"], "since": "@level_start"},
        ).passed


class TestHeadOfficeRef:
    """What Head Office really holds, which the local snapshot cannot see."""

    @pytest.fixture
    def office(self, tmp_path, linear_repo):  # type: ignore[no-untyped-def]
        bare = tmp_path / "head-office.git"
        linear_repo.git("init", "--bare", "-b", "main", str(bare))
        linear_repo.git("remote", "add", "origin", str(bare))
        linear_repo.git("push", "-u", "origin", "main")
        return linear_repo

    def grade(self, repo, args):  # type: ignore[no-untyped-def]
        from git_tutorial.predicates.base import EvalContext, evaluate

        probe = repo.probe()
        with probe.blobs() as blobs:
            return evaluate("head_office_ref", EvalContext(snapshot=probe.snapshot(),
                                                           blobs=blobs), args)

    def test_a_pushed_branch_is_there(self, office) -> None:  # type: ignore[no-untyped-def]
        office.git("push", "origin", "main:peak-rota")
        assert self.grade(office, {"ref": "refs/heads/peak-rota"}).passed

    def test_a_branch_deleted_there_is_gone(self, office) -> None:  # type: ignore[no-untyped-def]
        office.git("push", "origin", "main:peak-rota")
        office.git("push", "origin", "--delete", "peak-rota")
        assert self.grade(office, {"ref": "refs/heads/peak-rota", "exists": False}).passed

    def test_a_tag_on_the_wrong_commit_fails(self, office) -> None:  # type: ignore[no-untyped-def]
        office.git("tag", "stocktake-march", "HEAD~1")
        office.git("push", "origin", "stocktake-march")
        result = self.grade(office, {"ref": "refs/tags/stocktake-march", "at": "HEAD"})
        assert not result.passed and "Head Office has tag stocktake-march" in result.found

    def test_without_a_local_origin_it_is_an_authoring_error(  # type: ignore[no-untyped-def]
        self, linear_repo
    ) -> None:
        assert self.grade(linear_repo, {"ref": "refs/heads/main"}).error


class TestConflictChecks:
    def grade(self, repo, kind, args):  # type: ignore[no-untyped-def]
        from git_tutorial.predicates.base import EvalContext, evaluate

        probe = repo.probe()
        with probe.blobs() as blobs:
            return evaluate(kind, EvalContext(snapshot=probe.snapshot(), blobs=blobs), args)

    def test_markers_committed_in_any_file_fail(self, linear_repo) -> None:  # type: ignore[no-untyped-def]
        assert self.grade(linear_repo, "no_conflict_markers", {}).passed
        linear_repo.write("notes.md", "<<<<<<< HEAD\nours\n=======\ntheirs\n>>>>>>> main\n")
        linear_repo.add("notes.md").commit("oops")
        result = self.grade(linear_repo, "no_conflict_markers", {})
        assert not result.passed and "notes.md" in result.found

    def test_a_marker_lookalike_mid_line_is_fine(self, linear_repo) -> None:  # type: ignore[no-untyped-def]
        linear_repo.write("notes.md", "the string <<<<<<< appears in prose\n")
        linear_repo.add("notes.md").commit("prose")
        assert self.grade(linear_repo, "no_conflict_markers", {}).passed

    def test_file_matches_another_commit(self, linear_repo) -> None:  # type: ignore[no-untyped-def]
        args = {"path": "chronicle/ledger.md", "against": "HEAD~1"}
        assert self.grade(linear_repo, "file_matches", args).passed
        args = {"path": "chronicle/ledger.md", "against": "HEAD~2"}
        assert not self.grade(linear_repo, "file_matches", args).passed
