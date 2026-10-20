from __future__ import annotations

import json
import os
import threading
from pathlib import Path

import pytest

from git_tutorial.errors import StateCorruptError
from git_tutorial.state import migrations, paths
from git_tutorial.state.lock import FileLock, StateLockTimeout
from git_tutorial.state.models import Progress
from git_tutorial.state.store import StateStore

pytestmark = pytest.mark.unit


class TestPaths:
    def test_home_honours_the_override(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.setenv(paths.ENV_HOME, str(tmp_path / "elsewhere"))
        assert paths.home() == tmp_path / "elsewhere"

    def test_home_defaults_under_the_user(self, monkeypatch) -> None:
        monkeypatch.delenv(paths.ENV_HOME, raising=False)
        assert paths.home() == Path.home() / ".gittutorial"

    def test_repo_key_is_stable_across_spellings(self, tmp_path: Path) -> None:
        repo = tmp_path / "quest"
        repo.mkdir()
        nested = repo / "notes"
        nested.mkdir()

        direct = paths.repo_key(repo)
        assert paths.repo_key(Path(str(repo) + "/")) == direct
        assert paths.repo_key(Path(os.path.realpath(repo))) == direct

    def test_repo_key_follows_symlinks(self, tmp_path: Path) -> None:
        real = tmp_path / "real"
        real.mkdir()
        link = tmp_path / "link"
        link.symlink_to(real)
        assert paths.repo_key(link) == paths.repo_key(real)

    def test_repo_key_distinguishes_repos_and_names_them(self, tmp_path: Path) -> None:
        a, b = tmp_path / "alpha", tmp_path / "beta"
        a.mkdir()
        b.mkdir()
        assert paths.repo_key(a) != paths.repo_key(b)
        assert paths.repo_key(a).startswith("alpha-")


@pytest.fixture
def store(tmp_path: Path, monkeypatch) -> StateStore:
    monkeypatch.setenv(paths.ENV_HOME, str(tmp_path / "home"))
    worktree = tmp_path / "quest"
    worktree.mkdir()
    return StateStore(worktree)


class TestStore:
    def test_round_trips_every_field(self, store: StateStore) -> None:
        with store.mutate() as progress:
            progress.pack_id = "git-tutorial-levels"
            progress.current_level_id = "act1-01"
            progress.completed.append("act1-00")
            progress.add_recap(1.0, "You reached First Light.")
            entry = progress.for_level("act1-01")
            entry.start_head = "abc123"
            entry.hints_shown.append(0)
            entry.answers["branch"] = "main"
            entry.start_worktree["notes/ledger.md"] = "deadbeef"

        loaded = store.load()
        assert loaded.pack_id == "git-tutorial-levels"
        assert loaded.current_level_id == "act1-01"
        assert loaded.completed == ["act1-00"]
        assert loaded.recent_recap() == ("You reached First Light.",)
        restored = loaded.for_level("act1-01")
        assert restored.start_head == "abc123"
        assert restored.answers == {"branch": "main"}
        assert restored.start_worktree == {"notes/ledger.md": "deadbeef"}

    def test_absent_file_loads_a_default(self, store: StateStore) -> None:
        assert not store.exists()
        assert store.load().current_level_id is None

    def test_unknown_keys_survive_a_round_trip(self, store: StateStore) -> None:
        """An older engine must not silently delete a newer one's fields."""
        store.save(Progress())
        raw = json.loads(store.progress_path.read_text())
        raw["future_field"] = {"kept": True}
        store.progress_path.write_text(json.dumps(raw))

        store.save(store.load())
        assert json.loads(store.progress_path.read_text())["future_field"] == {"kept": True}

    def test_a_failed_replace_leaves_the_original_intact(
        self, store: StateStore, monkeypatch
    ) -> None:
        store.save(Progress(current_level_id="original"))
        before = store.progress_path.read_bytes()

        def boom(*_args: object, **_kwargs: object) -> None:
            raise OSError("disk full")

        monkeypatch.setattr(os, "replace", boom)
        with pytest.raises(OSError):
            store.save(Progress(current_level_id="clobbered"))

        assert store.progress_path.read_bytes() == before
        leftovers = list(store.progress_path.parent.glob("*.tmp"))
        assert leftovers == []

    def test_corrupt_json_is_quarantined_not_fatal(self, store: StateStore) -> None:
        """Losing progress is bad; being unable to play at all is worse."""
        store.save(Progress(current_level_id="act1-01"))
        store.progress_path.write_text("{not json", encoding="utf-8")

        recovered = store.load()
        assert recovered.current_level_id is None
        assert store.recovered_from_corruption
        assert list(store.directory.glob("progress.json.corrupt-*"))

    def test_cursors_are_a_separate_file(self, store: StateStore) -> None:
        store.save(Progress())
        assert not store.cursors_path.exists()


class TestLocking:
    def test_concurrent_mutations_do_not_lose_an_update(self, store: StateStore) -> None:
        store.save(Progress())
        barrier = threading.Barrier(2)

        def append(name: str) -> None:
            barrier.wait()
            with store.mutate() as progress:
                progress.completed.append(name)

        threads = [threading.Thread(target=append, args=(f"level-{i}",)) for i in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert sorted(store.load().completed) == ["level-0", "level-1"]

    def test_a_held_lock_times_out_with_an_actionable_message(self, store: StateStore) -> None:
        lock_path = store.directory / ".lock"
        with FileLock(lock_path), pytest.raises(StateLockTimeout, match="another gq command"):
            FileLock(lock_path, timeout=0.2).acquire()

    def test_the_lock_is_released_when_the_body_raises(self, store: StateStore) -> None:
        with pytest.raises(ValueError), store.mutate():
            raise ValueError("boom")
        with store.mutate() as progress:  # would block forever if still held
            progress.pack_id = "ok"


class TestMigrations:
    def test_a_newer_schema_is_refused_by_name(self) -> None:
        with pytest.raises(StateCorruptError, match="99"):
            migrations.migrate({"schema_version": 99})

    def test_a_registered_migration_runs(self, monkeypatch) -> None:
        def upgrade(raw: dict) -> dict:
            raw["schema_version"] = 1
            raw["migrated"] = True
            return raw

        monkeypatch.setitem(migrations.MIGRATIONS, 0, upgrade)
        out = migrations.migrate({"schema_version": 0})
        assert out["migrated"] is True
        assert out["schema_version"] == 1

    def test_an_old_file_with_no_path_forward_is_accepted(self) -> None:
        out = migrations.migrate({"schema_version": 0})
        assert out["schema_version"] == migrations.SCHEMA_VERSION
