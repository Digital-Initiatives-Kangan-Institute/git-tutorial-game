from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from git_tutorial.levels.pack import (
    LevelFormatMismatch,
    LevelPackNotFound,
    discover_pack,
    sibling_checkout,
)
from git_tutorial.state import paths

pytestmark = pytest.mark.unit


def make_pack(root: Path, *, format_version: int = 1) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "manifest.yaml").write_text(
        textwrap.dedent(f"""\
            pack_id: test-pack
            pack_version: "0.0.1"
            format_version: {format_version}
            workspace_dir: the-chronicle
            acts: []
            """),
        encoding="utf-8",
    )
    return root


class TestPrecedence:
    def test_explicit_wins(self, tmp_path: Path, monkeypatch) -> None:
        wanted = make_pack(tmp_path / "wanted")
        monkeypatch.setenv(paths.ENV_LEVELS, str(make_pack(tmp_path / "env")))
        assert discover_pack(wanted).root == wanted.resolve()

    def test_the_environment_beats_the_implicit_sources(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        wanted = make_pack(tmp_path / "env")
        monkeypatch.setenv(paths.ENV_LEVELS, str(wanted))
        monkeypatch.setenv(paths.ENV_HOME, str(tmp_path / "home"))
        make_pack(tmp_path / "home" / "levels")
        assert discover_pack().root == wanted.resolve()

    def test_the_sibling_checkout_beats_a_stray_clone(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """What the player launched wins over whatever is in ~/.gittutorial."""
        monkeypatch.delenv(paths.ENV_LEVELS, raising=False)
        monkeypatch.setenv(paths.ENV_HOME, str(tmp_path / "home"))
        clone = make_pack(tmp_path / "home" / "levels")

        sibling = sibling_checkout()
        if sibling is None:
            pytest.skip("not running from a source checkout")

        found = discover_pack().root
        assert found == sibling
        assert found != clone.resolve()


class TestExplicitSourcesFailLoudly:
    def test_a_levels_flag_pointing_nowhere_is_an_error(self, tmp_path: Path) -> None:
        """Silently loading a different pack is the worst possible outcome for
        a content author."""
        empty = tmp_path / "empty"
        empty.mkdir()
        with pytest.raises(LevelPackNotFound, match="--levels"):
            discover_pack(empty)

    def test_an_environment_pointing_nowhere_is_an_error(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        empty = tmp_path / "empty"
        empty.mkdir()
        monkeypatch.setenv(paths.ENV_LEVELS, str(empty))
        with pytest.raises(LevelPackNotFound, match=paths.ENV_LEVELS):
            discover_pack()

    def test_a_format_mismatch_names_both_sides(self, tmp_path: Path) -> None:
        future = make_pack(tmp_path / "future", format_version=99)
        with pytest.raises(LevelFormatMismatch) as caught:
            discover_pack(future)
        assert "99" in str(caught.value)
        assert "upgrade" in str(caught.value).lower()


class TestNotFound:
    def test_the_message_points_at_the_launcher_not_pip(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """play.sh is the only way in; advising pip would send a beginner
        somewhere that no longer exists."""
        monkeypatch.delenv(paths.ENV_LEVELS, raising=False)
        monkeypatch.setenv(paths.ENV_HOME, str(tmp_path / "home"))
        monkeypatch.setattr("git_tutorial.levels.pack.sibling_checkout", lambda: None)

        with pytest.raises(LevelPackNotFound) as caught:
            discover_pack()

        message = str(caught.value)
        assert "play.sh" in message
        assert "pip install" not in message


class TestSiblingCheckout:
    def test_it_finds_the_levels_repo_in_this_checkout(self) -> None:
        found = sibling_checkout()
        if found is None:
            pytest.skip("not running from a source checkout")
        assert (found / "manifest.yaml").exists()
        assert found.name == "git_tutorial_content"
