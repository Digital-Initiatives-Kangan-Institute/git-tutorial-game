#!/usr/bin/env python3
"""Build `wt.pyz`: the whole tutorial in one file.

    python3 tools/build_zipapp.py              # -> dist/wt.pyz
    python3 tools/build_zipapp.py --out /tmp/wt.pyz

What goes in: the engine, the level pack with its history bundle, and
PyYAML. What stays out: anything compiled. PyYAML guards its C loader with
`try: from .cyaml import * / except ImportError`, so dropping the `_yaml`
extension leaves the pure-Python parser and an archive that runs on any
machine rather than only on the one that built it.

The result needs python3 and git on the player's machine and nothing else -
no pip, no virtualenv, no network. `wt doctor` checks for both and says so
plainly when one is missing.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import zipapp
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT / "engine" / "src" / "git_tutorial"
LEVELS = ROOT / "content" / "src" / "git_tutorial_content"

# Compiled caches, editor droppings and the pack's own test fixtures. None
# of it is read at play time and all of it is dead weight in the archive.
SKIP = shutil.ignore_patterns(
    "__pycache__", "*.pyc", "*.pyo", "*.egg-info", ".DS_Store", ".pytest_cache",
)

MAIN = '''\
# Written by tools/build_zipapp.py
import sys

from git_tutorial.cli import main

sys.exit(main())
'''


def stage(into: Path) -> None:
    into.mkdir(parents=True)
    shutil.copytree(ENGINE, into / "git_tutorial", ignore=SKIP)
    shutil.copytree(LEVELS, into / "git_tutorial_content", ignore=SKIP)
    (into / "__main__.py").write_text(MAIN, encoding="utf-8")
    _vendor_yaml(into)


def _vendor_yaml(into: Path) -> None:
    """PyYAML, without the part that is compiled for one machine."""
    try:
        import yaml
    except ImportError:  # pragma: no cover - the build machine needs it
        sys.exit(
            "PyYAML is needed to build the archive (it is what gets vendored).\n"
            "  pip install PyYAML"
        )

    source = Path(yaml.__file__).parent
    shutil.copytree(source, into / "yaml", ignore=SKIP)
    # `yaml/cyaml.py` imports the extension; the package already falls back
    # when that fails, so the file can stay and the .so cannot come.
    for compiled in (into / "yaml").glob("*.so"):
        compiled.unlink()
    for compiled in (into / "yaml").glob("*.pyd"):
        compiled.unlink()


def build(out: Path) -> Path:
    staging = out.parent / f".{out.name}.staging"
    shutil.rmtree(staging, ignore_errors=True)
    out.parent.mkdir(parents=True, exist_ok=True)

    try:
        stage(staging)
        zipapp.create_archive(
            staging,
            target=out,
            interpreter="/usr/bin/env python3",
            compressed=True,
        )
    finally:
        shutil.rmtree(staging, ignore_errors=True)

    out.chmod(0o755)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out", default=str(ROOT / "dist" / "wt.pyz"), help="where to write the archive"
    )
    args = parser.parse_args(argv)

    archive = build(Path(args.out).expanduser().resolve())
    size = archive.stat().st_size / 1024
    print(f"wrote {archive} ({size:.0f} KB)")
    print()
    print("  python3 wt.pyz doctor      check the machine")
    print("  python3 wt.pyz start       make a workspace here")
    print("  python3 wt.pyz             the watcher and browser view, in the workspace")
    return 0


if __name__ == "__main__":
    sys.exit(main())
