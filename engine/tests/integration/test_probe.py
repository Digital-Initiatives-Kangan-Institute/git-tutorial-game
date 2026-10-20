from __future__ import annotations

import random
from pathlib import Path

import pytest

from git_tutorial.testing.builder import RepoBuilder

pytestmark = pytest.mark.integration


def test_snapshot_reports_branch_head_and_graph(linear_repo: RepoBuilder) -> None:
    snap = linear_repo.snapshot()

    assert snap.head_ref == "main"
    assert not snap.detached
    assert snap.branches["main"] == snap.head_sha
    assert len(snap.graph) == 3
    assert snap.is_clean
    assert snap.index_blobs.keys() == {"chronicle/ledger.md", "chronicle/index.md"}


def test_detached_head_is_detected(linear_repo: RepoBuilder) -> None:
    linear_repo.detach("HEAD~1")
    snap = linear_repo.snapshot()

    assert snap.detached
    assert snap.head_ref is None


def test_reflog_keeps_unreachable_commits_in_the_graph(linear_repo: RepoBuilder) -> None:
    """Regression guard for `rev-list --reflog`.

    Every Act 3 level asserts over commits left unreachable by `reset --hard`.
    Without --reflog those commits vanish from the graph and every one of those
    predicates silently returns False on a student's machine.
    """
    lost = linear_repo.git("rev-parse", "HEAD").stdout.strip()
    linear_repo.reset("HEAD~2", "hard")

    snap = linear_repo.snapshot()

    assert lost not in snap.branches.values()
    assert lost in snap.graph, "unreachable commit missing — is --reflog still on rev-list?"
    assert snap.graph.require(lost).subject == "add an index"


def test_tutorial_refs_are_collected_but_are_not_branches(linear_repo: RepoBuilder) -> None:
    linear_repo.tutorial_ref("aldren-seal", "HEAD~1")
    snap = linear_repo.snapshot()

    assert "aldren-seal" in snap.tutorial_refs
    assert "aldren-seal" not in snap.branches


def test_annotated_tag_resolves_to_its_commit(linear_repo: RepoBuilder) -> None:
    linear_repo.git("tag", "-a", "v1", "-m", "the first seal")
    snap = linear_repo.snapshot()

    assert snap.tags["v1"] == snap.head_sha


def test_special_refs_expose_orig_head(linear_repo: RepoBuilder) -> None:
    linear_repo.reset("HEAD~1", "hard")
    snap = linear_repo.snapshot()

    assert "ORIG_HEAD" in snap.special_refs


def test_in_progress_reports_a_paused_merge(repo: RepoBuilder) -> None:
    repo.write("ledger.md", "base\n").commit("base")
    repo.branch("other")
    repo.write("ledger.md", "main says this\n").commit("main edit")
    repo.switch("other")
    repo.write("ledger.md", "other says this\n").commit("other edit")
    repo.git("merge", "main", check=False)

    snap = repo.snapshot()

    assert "MERGE_HEAD" in snap.in_progress
    assert any(e.kind == "unmerged" for e in snap.status)


def test_dirty_worktree_blob_differs_from_index(linear_repo: RepoBuilder) -> None:
    linear_repo.write("chronicle/ledger.md", "edited but not staged\n")
    snap = linear_repo.snapshot()

    path = "chronicle/ledger.md"
    assert path in snap.worktree_blobs
    assert snap.worktree_blobs[path] != snap.index_blobs[path]
    assert not snap.is_clean


def test_stash_count(linear_repo: RepoBuilder) -> None:
    assert linear_repo.snapshot().stash_count == 0
    linear_repo.write("chronicle/ledger.md", "work in progress\n").stash()
    assert linear_repo.snapshot().stash_count == 1


def test_untracked_files_do_not_make_the_tree_dirty(linear_repo: RepoBuilder) -> None:
    linear_repo.write("scratch.txt", "notes\n")
    snap = linear_repo.snapshot()

    assert snap.is_clean
    assert any(e.kind == "untracked" and e.path == "scratch.txt" for e in snap.status)


class TestFingerprint:
    def test_index_lock_skips_the_tick(self, linear_repo: RepoBuilder) -> None:
        probe = linear_repo.probe()
        assert probe.fingerprint() is not None

        (probe.git_dir / "index.lock").write_text("", encoding="utf-8")
        assert probe.fingerprint() is None, "a mid-write repo must not be read"

    def test_branch_creation_changes_the_fingerprint(self, linear_repo: RepoBuilder) -> None:
        """`git branch` touches neither HEAD nor the index, which is why the
        spec's three-file stat list is not enough."""
        probe = linear_repo.probe()
        before = probe.fingerprint()

        linear_repo.branch("rescue")
        after = probe.fingerprint()

        assert after is not None
        assert after.changed_from(before)

    def test_forced_refresh_defeats_a_coarse_mtime_clock(self, linear_repo: RepoBuilder) -> None:
        probe = linear_repo.probe()
        forced = [bool(probe.fingerprint().forced) for _ in range(15)]  # type: ignore[union-attr]
        assert forced[-1] is True
        assert sum(forced) == 1


class TestDeterminism:
    def test_identical_scripts_produce_identical_shas(self, tmp_path: Path) -> None:
        def build(name: str) -> str:
            builder = RepoBuilder(tmp_path / name, home=tmp_path / f"home-{name}").init()
            builder.write("chronicle/ledger.md", "the first entry\n")
            builder.commit("open the chronicle")
            builder.write("chronicle/ledger.md", "the first entry\nthe second\n")
            return builder.commit("continue it")

        assert build("a") == build("b")

    def test_shas_are_pinned_across_machines(self, tmp_path: Path) -> None:
        builder = RepoBuilder(tmp_path / "pinned", home=tmp_path / "home").init()
        builder.write("chronicle/ledger.md", "the first entry\n")
        sha = builder.commit("open the chronicle")

        assert sha == "923b6c69e359749daf80b758855d02ca2c0b4312"


class TestGraphAgainstRealGit:
    @pytest.mark.parametrize("seed", range(12))
    def test_is_ancestor_matches_merge_base(self, tmp_path: Path, seed: int) -> None:
        """Ancestry is computed in-process so predicates stay pure, which only
        works if it agrees with git itself."""
        rng = random.Random(seed)
        builder = RepoBuilder(tmp_path / f"r{seed}", home=tmp_path / "home").init()

        shas = [builder.write("f.txt", "0\n").commit("c0")]
        for i in range(1, 9):
            if rng.random() < 0.35 and len(shas) > 2:
                builder.detach(rng.choice(shas[:-1]))
            shas.append(builder.write("f.txt", f"{i}\n").commit(f"c{i}"))

        graph = builder.snapshot().graph
        for _ in range(20):
            a, b = rng.choice(shas), rng.choice(shas)
            expected = builder.git(
                "merge-base", "--is-ancestor", a, b, check=False
            ).returncode == 0
            assert graph.is_ancestor(a, b) is expected, f"{a[:8]} -> {b[:8]}"
