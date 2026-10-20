from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from git_tutorial.errors import LevelAuthoringError, TutorialError
from git_tutorial.levels.loader import load_level
from git_tutorial.levels.model import Level
from git_tutorial.state import paths
from git_tutorial.version import LEVEL_FORMAT_VERSION

MANIFEST = "manifest.yaml"
BUNDLE = "depot.bundle"
SHA_MANIFEST = "sha_manifest.json"


class LevelPackNotFound(TutorialError):
    pass


class LevelFormatMismatch(TutorialError):
    pass


@dataclass(frozen=True, slots=True)
class PackLevelEntry:
    id: str
    act: int
    level: int
    rel_path: str
    required: bool = True


@dataclass(frozen=True, slots=True)
class ActEntry:
    act: int
    title: str
    level_ids: tuple[str, ...]
    subject: str = ""  # what the act teaches, beside its story title


@dataclass
class LevelPack:
    root: Path  # always a real filesystem path
    pack_id: str
    pack_version: str
    format_version: int
    workspace_dir_name: str
    acts: tuple[ActEntry, ...]
    entries: tuple[PackLevelEntry, ...]  # manifest order is play order
    source: str
    _levels: dict[str, Level] = field(default_factory=dict, repr=False)
    _shas: dict[str, str] | None = field(default=None, repr=False)

    def entry(self, level_id: str) -> PackLevelEntry:
        for candidate in self.entries:
            if candidate.id == level_id:
                return candidate
        raise LevelAuthoringError(f"no level {level_id!r} in pack {self.pack_id}")

    def level_dir(self, level_id: str) -> Path:
        return self.root / self.entry(level_id).rel_path

    def load(self, level_id: str) -> Level:
        cached = self._levels.get(level_id)
        if cached is None:
            cached = load_level(self.level_dir(level_id) / "level.yaml")
            self._levels[level_id] = cached
        return cached

    def first_level_id(self) -> str:
        if not self.entries:
            raise LevelAuthoringError(f"pack {self.pack_id} contains no levels")
        return self.entries[0].id

    def next_level_id(self, after: str, *, include_optional: bool = True) -> str | None:
        ids = [e.id for e in self.entries if include_optional or e.required]
        try:
            index = ids.index(after)
        except ValueError:
            return None
        return ids[index + 1] if index + 1 < len(ids) else None

    def act_of(self, level_id: str) -> ActEntry:
        for act in self.acts:
            if level_id in act.level_ids:
                return act
        raise LevelAuthoringError(f"level {level_id!r} belongs to no act")

    def position(self, level_id: str) -> tuple[int, int]:
        """(1-based index, total) in play order."""
        ids = [e.id for e in self.entries]
        return (ids.index(level_id) + 1, len(ids)) if level_id in ids else (0, len(ids))

    def sha(self, key: str) -> str | None:
        if self._shas is None:
            path = self.root / SHA_MANIFEST
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                raw = {}
            shas: dict[str, str] = {}
            for name, value in raw.items():
                shas[name] = value["sha"] if isinstance(value, dict) else str(value)
            self._shas = shas
        return self._shas.get(key)

    def shas(self) -> dict[str, str]:
        """Every commit key in sha_manifest.json, for prose substitution."""
        self.sha("")
        return dict(self._shas or {})

    def bundle_path(self) -> Path | None:
        candidate = self.root / BUNDLE
        return candidate if candidate.exists() else None

    def validate(self) -> list[str]:
        """Content-CI hook: returns human-readable problems, never raises."""
        problems: list[str] = []
        for entry in self.entries:
            directory = self.root / entry.rel_path
            if not (directory / "level.yaml").exists():
                problems.append(f"{entry.id}: no level.yaml at {entry.rel_path}")
                continue
            try:
                level = self.load(entry.id)
            except LevelAuthoringError as exc:
                problems.append(f"{entry.id}: {exc}")
                continue
            if level.id != entry.id:
                problems.append(f"{entry.id}: level.yaml declares id {level.id!r}")
            if not level.prose.brief:
                problems.append(f"{entry.id}: no prose.brief (gq status needs it)")
        return problems


def _read_manifest(root: Path, source: str) -> LevelPack:
    path = root / MANIFEST
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise LevelPackNotFound(f"could not read {path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise LevelPackNotFound(f"{path} is not a level pack manifest")

    format_version = int(raw.get("format_version", 0))
    pack_id = str(raw.get("pack_id", root.name))
    pack_version = str(raw.get("pack_version", "0"))

    if format_version != LEVEL_FORMAT_VERSION:
        raise LevelFormatMismatch(_mismatch_message(
            pack_id, pack_version, format_version, root, source
        ))

    acts: list[ActEntry] = []
    entries: list[PackLevelEntry] = []
    for act_raw in raw.get("acts") or []:
        act_no = int(act_raw["act"])
        ids: list[str] = []
        for level_raw in act_raw.get("levels") or []:
            entry = PackLevelEntry(
                id=str(level_raw["id"]),
                act=act_no,
                level=len(ids) + 1,
                rel_path=str(level_raw["path"]),
                required=bool(level_raw.get("required", True)),
            )
            entries.append(entry)
            ids.append(entry.id)
        acts.append(ActEntry(act=act_no, title=str(act_raw.get("title", f"Act {act_no}")),
                             level_ids=tuple(ids), subject=str(act_raw.get("subject", ""))))

    return LevelPack(
        root=root,
        pack_id=pack_id,
        pack_version=pack_version,
        format_version=format_version,
        workspace_dir_name=str(raw.get("workspace_dir", "tallowmere-ops")),
        acts=tuple(acts),
        entries=tuple(entries),
        source=source,
    )


def _mismatch_message(
    pack_id: str, pack_version: str, pack_format: int, root: Path, source: str
) -> str:
    from git_tutorial.version import __version__

    if pack_format > LEVEL_FORMAT_VERSION:
        remedy = "Upgrade the engine:  pipx upgrade git-tutorial"
    else:
        remedy = f"Update the levels:    git -C {root} pull"
    return (
        f"This level pack needs level format {pack_format}; "
        f"this git-tutorial speaks {LEVEL_FORMAT_VERSION}.\n\n"
        f"    pack    {pack_id} {pack_version}  ({source})\n"
        f"    engine  git-tutorial {__version__}\n\n"
        f"  {remedy}"
    )


def sibling_checkout() -> Path | None:
    """The levels repo as it sits beside the engine in a source checkout.

    play.sh sets GITTUTORIAL_LEVELS explicitly, but a player who opens a second
    terminal and simply types `gq` has no environment set and should still
    find the levels rather than be told to install something.
    """
    #  .../git-tutorial/src/git_tutorial/levels/pack.py -> .../<container>
    container = Path(__file__).resolve().parents[4]
    candidate = container / "git-tutorial-levels" / "src" / "git_tutorial_content"
    return candidate if (candidate / MANIFEST).exists() else None


def bundled_pack() -> Path | None:
    """A pack shipped inside a zipapp, unpacked once to the game's home.

    `LevelPack.root` is a real filesystem path on purpose: prose is read
    from disk, setup scripts are imported from the pack root, and
    `solution.sh` is handed to bash by name. None of that works through a
    zip import, so a self-contained `gq.pyz` extracts its own copy of the
    pack the first time it runs and uses that from then on.

    Keyed by the archive's size and mtime, so a new build of the zipapp
    unpacks beside the old one rather than half over it.
    """
    from git_tutorial.portable import archive_of

    archive = archive_of("git_tutorial_content")
    if archive is None:
        return None
    try:
        stat = archive.stat()
    except OSError:
        return None

    stamp = f"{stat.st_size:x}-{stat.st_mtime_ns:x}"
    destination = paths.home() / "packs" / stamp
    root = destination / "git_tutorial_content"
    if (root / MANIFEST).exists():
        return root

    return _unpack(archive, destination, root)


def _unpack(archive: Path, destination: Path, root: Path) -> Path | None:
    """Extract the pack, then move it into place, so a half-written copy
    is never mistaken for a usable one by the next run."""
    import shutil
    import zipfile

    staging = destination.with_name(destination.name + ".partial")
    shutil.rmtree(staging, ignore_errors=True)
    try:
        with zipfile.ZipFile(archive) as bundle:
            members = [
                name for name in bundle.namelist()
                if name.startswith("git_tutorial_content/") and not name.endswith("/")
            ]
            if not members:
                return None
            bundle.extractall(staging, members)
        staging.parent.mkdir(parents=True, exist_ok=True)
        staging.replace(destination)
    except (OSError, zipfile.BadZipFile):
        shutil.rmtree(staging, ignore_errors=True)
        return None

    return root if (root / MANIFEST).exists() else None


def discover_pack(explicit: str | Path | None = None) -> LevelPack:
    """Explicit sources fail loudly; implicit ones fall through.

    A --levels flag that silently loads some other pack is the worst possible
    experience for a content author.
    """
    if explicit:
        root = Path(explicit).expanduser().resolve()
        if not (root / MANIFEST).exists():
            raise LevelPackNotFound(f"no {MANIFEST} in {root} (from --levels)")
        return _read_manifest(root, "--levels")

    env = os.environ.get(paths.ENV_LEVELS)
    if env:
        root = Path(env).expanduser().resolve()
        if not (root / MANIFEST).exists():
            raise LevelPackNotFound(f"no {MANIFEST} in {root} (from ${paths.ENV_LEVELS})")
        return _read_manifest(root, f"${paths.ENV_LEVELS}")

    # A pack shipped inside the same zipapp as this engine: the two were
    # built together, so it wins over anything found lying around.
    bundled = bundled_pack()
    if bundled is not None:
        return _read_manifest(bundled, "bundled in this build")

    # The checkout this engine is running from wins over a stray clone in
    # ~/.gittutorial: it is what the player actually launched.
    sibling = sibling_checkout()
    if sibling is not None:
        return _read_manifest(sibling, str(sibling))

    clone = paths.levels_clone_dir()
    if (clone / MANIFEST).exists():
        return _read_manifest(clone, str(clone))

    raise LevelPackNotFound(
        "no level pack found.\n\n"
        "  git-tutorial is started by its launcher, which knows where the\n"
        "  levels are:\n\n"
        "      ./play.sh\n\n"
        "  If the levels live somewhere unusual, say so:\n\n"
        "      gq --levels /path/to/git_tutorial_content"
    )
