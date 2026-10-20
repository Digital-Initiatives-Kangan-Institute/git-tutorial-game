from __future__ import annotations

from collections.abc import Callable, MutableMapping
from typing import Any

from git_tutorial.errors import StateCorruptError
from git_tutorial.state.models import SCHEMA_VERSION

# from-version -> upgrade function. Empty today; the hook and its test are what
# ship, so the first real migration is a data change rather than a design one.
MIGRATIONS: dict[int, Callable[[MutableMapping[str, Any]], MutableMapping[str, Any]]] = {}


def migrate(raw: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    version = int(raw.get("schema_version", 0))

    if version > SCHEMA_VERSION:
        raise StateCorruptError(
            f"this progress file was written by a newer git-tutorial "
            f"(format {version}; this build speaks {SCHEMA_VERSION}). "
            "Upgrade git-tutorial: pipx upgrade git-tutorial"
        )

    while version < SCHEMA_VERSION:
        upgrade = MIGRATIONS.get(version)
        if upgrade is None:
            # No path forward, but the data is not corrupt — stamp and accept.
            raw["schema_version"] = SCHEMA_VERSION
            return raw
        raw = upgrade(raw)
        new_version = int(raw.get("schema_version", version + 1))
        if new_version <= version:
            raise StateCorruptError(f"migration from format {version} did not advance the version")
        version = new_version

    return raw
