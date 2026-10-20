"""The single-file build, exercised by building it and playing from it.

A zipapp fails in ways no unit test sees: a file left out of the archive,
a pack that cannot be read through a zip import, a dependency that is only
on the build machine. So this builds the real artifact and runs the real
binary in a subprocess with a clean home.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

TOOLS = Path(__file__).resolve().parents[3] / "tools" / "build_zipapp.py"


def load_builder():  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location("build_zipapp", TOOLS)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def archive(tmp_path_factory: pytest.TempPathFactory) -> Path:
    if not TOOLS.exists():
        pytest.skip("not a source checkout")
    out = tmp_path_factory.mktemp("build") / "wt.pyz"
    return load_builder().build(out)  # type: ignore[no-any-return]


def run(archive: Path, *args: str, home: Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["GITTUTORIAL_HOME"] = str(home)
    # Both would let the subprocess find the checkout instead of the
    # archive, which is the one thing this test exists to rule out.
    env.pop("GITTUTORIAL_LEVELS", None)
    env.pop("PYTHONPATH", None)
    home.mkdir(parents=True, exist_ok=True)
    return subprocess.run(
        [sys.executable, str(archive), *args],
        capture_output=True, text=True, env=env, cwd=str(home), check=False,
    )


class TestTheArchive:
    def test_it_is_one_file_and_small(self, archive: Path) -> None:
        assert archive.is_file()
        assert archive.stat().st_size < 2 * 1024 * 1024, "a student downloads this"

    def test_nothing_compiled_rides_along(self, archive: Path) -> None:
        """A `.so` would pin the archive to the machine that built it."""
        import zipfile

        with zipfile.ZipFile(archive) as bundle:
            names = bundle.namelist()
        assert not [n for n in names if n.endswith((".so", ".pyd", ".pyc"))]
        assert any(n.startswith("yaml/") for n in names), "PyYAML must be vendored"
        assert "git_tutorial_content/depot.bundle" in names

    def test_it_runs_where_nothing_is_installed(
        self, archive: Path, tmp_path: Path
    ) -> None:
        result = run(archive, "doctor", home=tmp_path / "home")
        assert result.returncode == 0, result.stderr
        assert "running from" in result.stdout
        assert archive.name in result.stdout

    def test_the_pack_is_unpacked_and_then_reused(
        self, archive: Path, tmp_path: Path
    ) -> None:
        """Prose is read from disk and solution.sh is handed to bash, so the
        pack cannot stay inside the zip."""
        home = tmp_path / "home"

        first = run(archive, "start", home=home)
        assert first.returncode == 0, first.stderr

        packs = list((home / "packs").iterdir())
        assert len(packs) == 1, "unpacked once, under a name keyed to this build"
        stamp = packs[0].stat().st_mtime_ns

        workspace = home / "tallowmere-ops"
        again = run(archive, "--repo", str(workspace), "check", home=home)
        assert "JOB-101" in again.stdout, again.stderr

        assert [p.name for p in (home / "packs").iterdir()] == [packs[0].name]
        assert packs[0].stat().st_mtime_ns == stamp, "not re-unpacked every run"

    def test_a_workspace_can_be_started_and_checked(
        self, archive: Path, tmp_path: Path
    ) -> None:
        home = tmp_path / "home"
        home.mkdir(parents=True)

        started = run(archive, "start", home=home)
        assert started.returncode == 0, started.stderr

        workspace = home / "tallowmere-ops"
        assert (workspace / ".git").is_dir(), "a real clone, from the bundled history"

        checked = subprocess.run(
            [sys.executable, str(archive), "--repo", str(workspace), "check"],
            capture_output=True, text=True, check=False,
            env={**os.environ, "GITTUTORIAL_HOME": str(home),
                 "GITTUTORIAL_LEVELS": "", "PYTHONPATH": ""},
            cwd=str(workspace),
        )
        assert "read the shift handover" in checked.stdout.lower()

    def test_the_browser_page_is_served_from_inside_the_archive(
        self, archive: Path
    ) -> None:
        probe = (
            "import sys; sys.path.insert(0, sys.argv[1]);"
            "from git_tutorial.web.server import asset;"
            "print(*(len(asset(n)) for n in ('index.html', 'app.js', 'app.css')))"
        )
        result = subprocess.run(
            [sys.executable, "-c", probe, str(archive)],
            capture_output=True, text=True, check=False,
            env={**os.environ, "PYTHONPATH": ""}, cwd=str(archive.parent),
        )
        assert result.returncode == 0, result.stderr
        assert all(int(size) > 1000 for size in result.stdout.split())


class TestPortableDetection:
    def test_an_ordinary_import_is_not_an_archive(self) -> None:
        from git_tutorial import portable

        assert portable.archive_of("git_tutorial") is None
        assert portable.archive_path() is None

    def test_a_module_that_does_not_exist_is_not_an_archive(self) -> None:
        from git_tutorial import portable

        assert portable.archive_of("no_such_module_anywhere") is None
