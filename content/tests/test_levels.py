"""The level harness, per spec §12.

Every level ships solution.sh; CI runs setup -> solution -> assert-all-pass.
That same file is what `wt solve` executes, so the feature students rely on
when stuck cannot silently rot.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

from git_tutorial.checker import Checker
from git_tutorial.git.runner import GitRunner
from git_tutorial.levels.pack import discover_pack
from git_tutorial.predicates.base import EvalContext
from git_tutorial.session.lifecycle import Session
from git_tutorial.state.store import StateStore
from git_tutorial.testing.builder import RepoBuilder

PACK_ROOT = Path(__file__).resolve().parents[1] / "src" / "git_tutorial_content"
PACK = discover_pack(PACK_ROOT)
# Levels whose content exists. `test_every_manifest_entry_is_authored`
# keeps this from quietly shrinking.
LEVEL_IDS = [
    entry.id for entry in PACK.entries if (PACK.level_dir(entry.id) / "level.yaml").exists()
]

# Solutions that pipe anything: the only ones a long reflog can break.
PIPED_SOLUTIONS = [
    entry.id
    for entry in PACK.entries
    if entry.id in LEVEL_IDS
    and "|" in (PACK.level_dir(entry.id) / "solution.sh").read_text(encoding="utf-8")
]


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[RepoBuilder]:
    """A fresh clone of the authored history, as `wt start` would produce."""
    monkeypatch.setenv("GITTUTORIAL_HOME", str(tmp_path / "wthome"))
    monkeypatch.setenv("GITTUTORIAL_LEVELS", str(PACK_ROOT))

    archive = tmp_path / "head-office.git"
    archive.mkdir()
    bare = GitRunner(archive)
    bare.run("init", "--bare", "--object-format=sha1", "-b", "main")
    bare.run("fetch", str(PACK.bundle_path()),
             "+refs/heads/*:refs/heads/*", "+refs/tutorial/*:refs/tutorial/*")

    work = tmp_path / "workspace"
    GitRunner(tmp_path).run("clone", str(archive), str(work))
    runner = GitRunner(work)
    runner.run("config", "--add", "remote.origin.fetch", "+refs/tutorial/*:refs/tutorial/*")
    runner.run("fetch", "origin")
    runner.run("config", "user.name", "Test Student")
    runner.run("config", "user.email", "student@example.invalid")
    # What `_configure_clone` sets in the real game. Without it `git pull`
    # fails on diverged branches, and act 4's levels would pass here and
    # fail in front of a student - the same gap the reflog padding closes.
    runner.run("config", "pull.rebase", "false")

    yield RepoBuilder(work, deterministic=False)


def _session(repo: RepoBuilder) -> Session:
    return Session(
        worktree=repo.path,
        probe=repo.probe(),
        repo=repo,
        pack=discover_pack(PACK_ROOT),
        store=StateStore(repo.path),
    )


def _setup(level_id: str, repo: RepoBuilder) -> None:
    """Go through Session, so the harness exercises the path students take."""
    _session(repo).begin_level(level_id)


def _typed(level_id: str, repo: RepoBuilder) -> dict[str, str]:
    """What the solution typed with `wt answer`, read back from progress."""
    return dict(_session(repo).progress.for_level(level_id).answers)


def _report(level_id: str, repo: RepoBuilder, answers: dict[str, str] | None = None):
    level = PACK.load(level_id)
    probe = repo.probe()
    # The reflog window the level opened at setup, read back from the same
    # store the game uses. Without it every `used_command` fails and every
    # `not_used_command` passes, whatever the solution did - so a technique
    # assertion would be graded here by not being graded at all.
    entry = _session(repo).progress.for_level(level_id)
    with probe.blobs() as blobs:
        snapshot = probe.snapshot()
        ctx = EvalContext(
            snapshot=snapshot,
            blobs=blobs,
            events=probe.events(),
            level_start_sha=snapshot.head_sha,
            level_start_offsets=entry.start_offsets,
            technique=level.technique,
            answers=answers or {},
        )
        return Checker.evaluate(level, ctx)


def _run_solution(level_id: str, repo: RepoBuilder) -> subprocess.CompletedProcess[bytes]:
    level = PACK.load(level_id)
    script = level.directory / (level.solution or "solution.sh")
    env = dict(os.environ)
    env["GITTUTORIAL_LEVELS"] = str(PACK.root)
    # `wt` must be callable: solution scripts answer with `wt answer`, and
    # they are the same artifact `wt solve` runs for a stuck student.
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    # Author dates deliberately unset: student commits must vary, so any
    # assertion that accidentally depends on a student sha flakes at once.
    for key in ("GIT_AUTHOR_DATE", "GIT_COMMITTER_DATE"):
        env.pop(key, None)
    return subprocess.run(
        ["bash", str(script)], cwd=repo.path, env=env, capture_output=True, check=False
    )


def _pad_reflog(repo: RepoBuilder, lines: int = 400) -> None:
    """Make the reflog as long as a real playthrough's, cheaply.

    Written straight into the file rather than made by git: four hundred
    real commands would cost more than the rest of this suite. Appended
    before setup runs, so the level's own entries are still the newest and
    anything a solution says about `HEAD@{1}` still means what it meant.
    """
    sha = repo.git("rev-parse", "HEAD").stdout.strip()
    who = "Test Student <student@example.invalid> 1700000000 +0000"
    path = repo.path / ".git" / "logs" / "HEAD"
    with path.open("a", encoding="utf-8") as handle:
        for _ in range(lines):
            handle.write(f"{sha} {sha} {who}\tcheckout: moving from main to main\n")


def _fingerprint(repo: RepoBuilder) -> str:
    git = repo.git
    # A level may hand the student a paused merge, and `write-tree` cannot
    # build a tree from an unmerged index. The porcelain-v2 status below
    # records every stage of every conflicted path, so dropping the tree
    # there costs the fingerprint nothing.
    tree = git("write-tree", check=False)
    parts = [
        git("for-each-ref", "--format=%(refname) %(objectname)").stdout,
        git("rev-parse", "HEAD").stdout,
        tree.stdout if tree.returncode == 0 else "(unmerged index)",
        git("status", "--porcelain=v2", "--untracked-files=all").stdout,
        git("stash", "list").stdout,
    ]
    return "\n".join(parts)


class TestEveryLevel:
    @pytest.mark.parametrize("level_id", LEVEL_IDS)
    def test_setup_is_idempotent(self, level_id: str, workspace: RepoBuilder) -> None:
        _setup(level_id, workspace)
        before = _fingerprint(workspace)
        _setup(level_id, workspace)
        assert _fingerprint(workspace) == before

    @pytest.mark.parametrize("level_id", LEVEL_IDS)
    def test_the_level_is_not_already_solved(self, level_id: str, workspace: RepoBuilder) -> None:
        """A level satisfied at setup time asserts nothing."""
        _setup(level_id, workspace)
        report = _report(level_id, workspace)
        assert report.results, f"{level_id} has no assertions"
        assert not report.complete, f"{level_id} is already solved the moment it begins"

    @pytest.mark.parametrize("level_id", LEVEL_IDS)
    def test_the_solution_completes_the_level(
        self, level_id: str, workspace: RepoBuilder
    ) -> None:
        """setup -> solution -> every assertion passes.

        This is the test spec 12 calls the highest-value one in the project,
        and it was missing: the harness only ever checked that solution.sh
        exited 0, so a level whose assertions could never pass shipped green.
        """
        _setup(level_id, workspace)
        result = _run_solution(level_id, workspace)
        assert result.returncode == 0, (result.stdout + result.stderr).decode()

        report = _report(level_id, workspace, _typed(level_id, workspace))
        failing = [r.label or r.kind for r in report.results if r.blocking]
        assert report.complete, f"{level_id} still failing after its own solution: {failing}"

    @pytest.mark.parametrize("level_id", PIPED_SOLUTIONS)
    def test_a_solution_survives_a_long_reflog(
        self, level_id: str, workspace: RepoBuilder
    ) -> None:
        """A fresh clone's reflog is five lines; a student reaching act 3 has
        a hundred and fifty.

        That difference hid a real bug. `git reflog | awk '...{exit}'` closes
        the pipe while git is still writing, and under `set -o pipefail` the
        SIGPIPE becomes an exit status of 141 - so four act 3 solutions
        passed every test here and failed in the actual game. Only levels
        whose solution pipes anything are run, because they are the only ones
        that can fail this way and each run costs a solution.
        """
        _pad_reflog(workspace)
        _setup(level_id, workspace)
        result = _run_solution(level_id, workspace)
        assert result.returncode == 0, (
            f"{level_id}'s solution fails against a realistic reflog: "
            f"{result.stderr.decode() or f'exit {result.returncode}'}"
        )

    @pytest.mark.parametrize("level_id", LEVEL_IDS)
    def test_reset_midway_then_solving_still_works(
        self, level_id: str, workspace: RepoBuilder
    ) -> None:
        """The real reset path, which a simple double-run misses."""
        _setup(level_id, workspace)
        workspace.write("half-finished.txt", "a student's abandoned attempt\n")
        _setup(level_id, workspace)
        assert _run_solution(level_id, workspace).returncode == 0


class TestSolutions:
    def test_level_one_is_answered_from_the_repository(self, workspace: RepoBuilder) -> None:
        """Answered the way a student reads them - not from the level's own
        expected values, which is how a wrong answer key once passed CI."""
        level_id = "act1-01-shift-handover"
        _setup(level_id, workspace)
        session = _session(workspace)
        oldest_first = workspace.git("rev-list", "--reverse", "HEAD").stdout.split()
        typed = {
            "branch": workspace.git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip(),
            "count": workspace.git("rev-list", "--count", "HEAD").stdout.strip(),
            "second": workspace.git("rev-parse", "--short", oldest_first[1]).stdout.strip(),
            "author": workspace.git("log", "-1", "--format=%an").stdout.strip().split()[0],
        }
        for key, value in typed.items():
            session.record_answer(key, value)
        assert _report(level_id, workspace, _typed(level_id, workspace)).complete

    def test_the_working_tree_is_clean_the_moment_the_course_starts(
        self, workspace: RepoBuilder
    ) -> None:
        """A beginner's first `git status` should say the reassuring thing,
        with no untracked noise to explain away."""
        _setup("act1-01-shift-handover", workspace)
        assert workspace.git("status", "--porcelain").stdout.strip() == ""

    def test_the_engine_writes_nothing_into_the_workspace(self, workspace: RepoBuilder) -> None:
        """Answers live in progress, outside the repository, so no level can
        trip over a file the tutorial left behind."""
        _setup("act1-01-shift-handover", workspace)
        _session(workspace).record_answer("branch", "main")
        assert workspace.git("status", "--porcelain", "--ignored").stdout.strip() == ""


class TestAnswerKeys:
    """Derive each answer from the repo, never from the same constant the
    level declares.

    The first version of these tests fed the level's own expected values back
    in, so an answer key that contradicted the repository passed CI and was
    only caught by a player being told a correct answer was wrong.
    """

    def test_the_declared_answers_match_the_actual_repository(
        self, workspace: RepoBuilder
    ) -> None:
        level_id = "act1-01-shift-handover"
        _setup(level_id, workspace)
        level = PACK.load(level_id)

        truth = {
            "branch": workspace.git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip(),
            "count": workspace.git("rev-list", "--count", "HEAD").stdout.strip(),
            "author": workspace.git("log", "-1", "--format=%an").stdout.strip().split()[0],
        }

        for spec in level.assertions:
            if spec.kind != "answer" or "equals" not in spec.args:
                continue
            key = str(spec.args["id"])
            if key not in truth:
                continue
            accepted = {str(spec.args["equals"]).casefold()}
            accepted |= {str(a).casefold() for a in spec.args.get("accepts", [])}
            assert truth[key].casefold() in accepted, (
                f"{level_id} Q[{key}]: the repository says {truth[key]!r}, "
                f"but the level accepts {sorted(accepted)}"
            )

    def test_a_commit_answer_resolves_to_the_commit_it_names(
        self, workspace: RepoBuilder
    ) -> None:
        level_id = "act1-01-shift-handover"
        _setup(level_id, workspace)
        level = PACK.load(level_id)

        # The second commit, counted from the oldest, as a player would.
        oldest_first = workspace.git("rev-list", "--reverse", "HEAD").stdout.split()
        expected = oldest_first[1]

        for spec in level.assertions:
            if spec.kind == "answer" and spec.args.get("id") == "second":
                named = str(spec.args["equals_commit"])
                ref = f"refs/tutorial/{named[len('tutorial:'):]}"
                assert workspace.git("rev-parse", ref).stdout.strip() == expected

    def test_act_two_counts_match_the_branches_it_builds(
        self, workspace: RepoBuilder
    ) -> None:
        """2.3 asks how far the branches have diverged. Those numbers come
        from a setup script, so they are exactly the kind of answer that
        drifts when the setup changes and nothing notices."""
        level_id = "act2-03-see-the-whole-floor"
        _setup(level_id, workspace)
        level = PACK.load(level_id)

        truth = {
            "ahead": workspace.git(
                "rev-list", "--count", "main..aisle-d-fitout").stdout.strip(),
            "behind": workspace.git(
                "rev-list", "--count", "aisle-d-fitout..main").stdout.strip(),
        }

        for spec in level.assertions:
            if spec.kind != "answer":
                continue
            key = str(spec.args["id"])
            if key in truth:
                assert str(spec.args["equals"]) == truth[key], (
                    f"2.3 Q[{key}]: the repository says {truth[key]}, "
                    f"the level says {spec.args['equals']}"
                )
            elif key == "base":
                named = str(spec.args["equals_commit"])
                ref = f"refs/tutorial/{named[len('tutorial:'):]}"
                base = workspace.git("merge-base", "main", "aisle-d-fitout").stdout.strip()
                assert workspace.git("rev-parse", ref).stdout.strip() == base, (
                    "2.3 Q[base]: the ref the level names is not the commit "
                    "the two branches actually share"
                )


class TestHistory:
    def test_the_bundle_reproduces_exactly(self) -> None:
        """An innocent edit that reflows the hashes must fail the build, not a
        student's answer key."""
        from git_tutorial_content.history import build

        assert build.main(["--check"]) == 0

    def test_every_tutorial_ref_a_level_names_exists(self, workspace: RepoBuilder) -> None:
        for level_id in LEVEL_IDS:
            for spec in PACK.load(level_id).assertions:
                for value in spec.args.values():
                    if isinstance(value, str) and value.startswith("tutorial:"):
                        ref = f"refs/tutorial/{value[len('tutorial:'):]}"
                        assert workspace.has_ref(ref), f"{level_id} names {value}, which is missing"


class TestPackHygiene:
    def test_the_pack_validates(self) -> None:
        assert PACK.validate() == []

    @pytest.mark.parametrize("level_id", LEVEL_IDS)
    def test_the_arrival_beat_ends_with_commands_to_try(self, level_id: str) -> None:
        from git_tutorial.content.prose import load_prose, parse_prose

        text = load_prose(PACK.load(level_id), "intro")
        assert text, f"{level_id} has no intro prose"
        assert parse_prose(text).try_blocks, f"{level_id}'s arrival beat has no `try:` block"

    @pytest.mark.parametrize("level_id", LEVEL_IDS)
    def test_hints_escalate_and_end_with_a_command(self, level_id: str) -> None:
        level = PACK.load(level_id)
        assert len(level.hints) >= 3, f"{level_id} needs a full escalation ladder"
        assert "git " in level.hints[-1].text, f"{level_id}'s last hint must name the command"

    @pytest.mark.parametrize("level_id", LEVEL_IDS)
    def test_hints_are_never_funny_at_a_stuck_student(self, level_id: str) -> None:
        for hint in PACK.load(level_id).hints:
            assert "!" not in hint.text, f"{level_id}: hints are sincere, always"

    @pytest.mark.parametrize("level_id", LEVEL_IDS)
    def test_solution_scripts_are_executable_bash(self, level_id: str) -> None:
        level = PACK.load(level_id)
        script = level.directory / (level.solution or "solution.sh")
        assert script.exists(), f"{level_id} ships no solution.sh"
        assert shutil.which("bash")
        check = subprocess.run(["bash", "-n", str(script)], capture_output=True, check=False)
        assert check.returncode == 0, check.stderr.decode()

    def test_no_level_mentions_the_old_game(self) -> None:
        """Ported from git-workspace: no `gq` commands, no answers.md."""
        import re

        pattern = re.compile(r"\bgq [a-z]|answers\.md|refs/quest|quest:")
        for level_id in LEVEL_IDS:
            for path in PACK.level_dir(level_id).rglob("*"):
                if path.suffix in (".yaml", ".md", ".sh", ".py"):
                    text = path.read_text(encoding="utf-8")
                    assert not pattern.search(text), f"{level_id}/{path.name} mentions the old game"

    def test_every_manifest_entry_is_authored(self) -> None:
        missing = [e.id for e in PACK.entries if e.id not in LEVEL_IDS]
        assert not missing, f"levels in the manifest with no content yet: {missing}"

    def test_no_level_hardcodes_a_sha(self) -> None:
        """Levels name a tutorial ref instead, so a rebuild cannot break them."""
        import re

        pattern = re.compile(r"\b[0-9a-f]{7,40}\b")
        for level_id in LEVEL_IDS:
            for path in PACK.level_dir(level_id).rglob("*"):
                if path.suffix not in (".yaml", ".md", ".sh"):
                    continue
                for line in path.read_text(encoding="utf-8").splitlines():
                    assert not pattern.search(line), f"{path.name}: hardcoded sha in {line!r}"
