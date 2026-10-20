"""Whether this engine is running out of a single-file archive.

`tools/build_zipapp.py` packs the engine, the level pack and PyYAML into
one `gq.pyz` that needs no pip, no virtualenv and no network. Two places
have to know: the pack, because its files have to be on a real disk before
prose can be read or `solution.sh` handed to bash, and `wt doctor`, which
would otherwise tell a player to put `gq` on their PATH when there is no
`gq` to put there.
"""

from __future__ import annotations

import importlib.util
import zipimport
from pathlib import Path


def archive_of(module: str) -> Path | None:
    """The zip a module is being imported from, or None for ordinary files."""
    try:
        spec = importlib.util.find_spec(module)
    except (ImportError, ValueError):
        return None
    if spec is None or not isinstance(spec.loader, zipimport.zipimporter):
        return None
    return Path(spec.loader.archive)


def archive_path() -> Path | None:
    """The `gq.pyz` this engine is running from, if it is one."""
    return archive_of("git_tutorial")
