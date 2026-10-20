from __future__ import annotations

import shutil
import subprocess
import textwrap
from collections.abc import Iterator
from pathlib import Path

import pytest

from git_tutorial.levels.pack import discover_pack
from git_tutorial.session.lifecycle import Session
from git_tutorial.state import paths
from git_tutorial.state.store import StateStore
from git_tutorial.testing.builder import RepoBuilder


def _git_version() -> tuple[int, ...]:
    binary = shutil.which("git")
    if binary is None:
        pytest.exit("git is required to run this test suite", returncode=1)
    raw = subprocess.run(
        [binary, "--version"], capture_output=True, text=True, check=True
    ).stdout.strip()
    return tuple(int("".join(c for c in p if c.isdigit()) or 0)
                 for p in raw.removeprefix("git version ").split("."))


@pytest.fixture(scope="session", autouse=True)
def require_modern_git() -> None:
    if _git_version() < (2, 23):
        pytest.skip("git 2.23+ required for switch/restore")


@pytest.fixture
def repo(tmp_path: Path) -> Iterator[RepoBuilder]:
    builder = RepoBuilder(tmp_path / "repo", home=tmp_path / "home").init()
    yield builder


@pytest.fixture
def linear_repo(repo: RepoBuilder) -> RepoBuilder:
    repo.write("chronicle/ledger.md", "the first entry\n").commit("open the chronicle")
    repo.write("chronicle/ledger.md", "the first entry\nthe second\n").commit("continue it")
    repo.write("chronicle/index.md", "an index\n").commit("add an index")
    return repo


def write_level(
    directory: Path,
    level_id: str,
    *,
    number: int,
    setup_body: str,
    assertions: str,
) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    # Built by joining rather than dedenting an f-string: only the first line
    # of an interpolated multi-line value inherits the literal's indentation.
    body = [
        f"id: {level_id}",
        "act: 1",
        f"level: {number}",
        f"title: Level {number}",
        "setup: setup.py",
        "prose:",
        "  intro: prose/intro.md",
        "  brief: prose/brief.md",
        "assert:",
        *(f"  {line}" for line in textwrap.dedent(assertions).strip().splitlines()),
        "hints:",
        '  - {after_idle: 180s, text: "first nudge"}',
        '  - {after_idle: 420s, text: "second nudge"}',
        "",
    ]
    (directory / "level.yaml").write_text("\n".join(body), encoding="utf-8")
    (directory / "setup.py").write_text(textwrap.dedent(setup_body), encoding="utf-8")
    prose = directory / "prose"
    prose.mkdir(exist_ok=True)
    (prose / "intro.md").write_text(f"Level {number} begins.\n\n  try:  git status\n", "utf-8")
    (prose / "brief.md").write_text(f"You are on level {number}.\n", encoding="utf-8")


@pytest.fixture
def pack_root(tmp_path: Path) -> Path:
    root = tmp_path / "pack"
    root.mkdir()
    (root / "manifest.yaml").write_text(
        textwrap.dedent("""\
            pack_id: test-pack
            pack_version: "0.0.1"
            format_version: 1
            workspace_dir: quest
            acts:
              - act: 1
                title: Testing
                levels:
                  - {id: level-1, path: levels/level-1}
                  - {id: level-2, path: levels/level-2}
            """),
        encoding="utf-8",
    )
    write_level(
        root / "levels" / "level-1",
        "level-1",
        number=1,
        setup_body="""
            def setup(repo, state):
                repo.delete_branch("rescue", force=True)
                repo.write_file("target.txt", "planted\\n")
        """,
        assertions="- {kind: branch_exists, name: rescue}\n",
    )
    write_level(
        root / "levels" / "level-2",
        "level-2",
        number=2,
        setup_body="""
            def setup(repo, state):
                repo.delete_branch("second", force=True)
        """,
        assertions="- {kind: branch_exists, name: second}\n",
    )
    return root


@pytest.fixture
def session(tmp_path: Path, pack_root: Path, monkeypatch) -> Session:
    monkeypatch.setenv(paths.ENV_HOME, str(tmp_path / "home"))
    repo = RepoBuilder(tmp_path / "quest", home=tmp_path / "githome").init()
    repo.write("seed.txt", "seed\n").commit("seed")

    worktree = repo.path
    return Session(
        worktree=worktree,
        probe=repo.probe(),
        repo=repo,
        pack=discover_pack(pack_root),
        store=StateStore(worktree),
    )
