#!/usr/bin/env python3
"""Build the practice repository's authored history, deterministically.

Every input to a commit sha is pinned here, because levels ask questions like
"what is the hash of the second commit?" and the answer must be identical on
every student's machine. Plumbing only: no porcelain, so no gitconfig, hook or
git-version behaviour can reach the objects.

    python -m git_tutorial_content.history.build          # rebuild in place
    python -m git_tutorial_content.history.build --check  # verify reproducibility
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

HERE = Path(__file__).parent
PACK_ROOT = HERE.parent
SCRIPT = HERE / "script.yaml"
FILES = HERE / "files"
BUNDLE_OUT = PACK_ROOT / "depot.bundle"
MANIFEST_OUT = PACK_ROOT / "sha_manifest.json"

TOKEN = re.compile(r"\{\{\s*(sha|short)\s*:\s*([^}\s]+)\s*\}\}")
SHORT_LEN = 7


@dataclass(frozen=True)
class Built:
    shas: dict[str, str]
    subjects: dict[str, str]


def _env(home: Path) -> dict[str, str]:
    """A scrubbed environment: no user config may influence an object hash."""
    return {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(home),
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_TERMINAL_PROMPT": "0",
        "LC_ALL": "C",
        "TZ": "UTC",
    }


class Git:
    def __init__(self, repo: Path, home: Path) -> None:
        self.repo = repo
        self.env = _env(home)

    def run(self, *args: str, stdin: bytes | None = None, env: dict[str, str] | None = None) -> str:
        full = dict(self.env)
        if env:
            full.update(env)
        result = subprocess.run(
            ["git", "-C", str(self.repo), *args],
            input=stdin, capture_output=True, env=full, check=True,
        )
        return result.stdout.decode("utf-8", errors="surrogateescape").strip()


def _render(text: str, shas: dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        kind, key = match.group(1), match.group(2)
        if key not in shas:
            raise SystemExit(
                f"build: {{{{{kind}:{key}}}}} refers to a commit that does not exist yet — "
                "a document cannot quote a commit it is contained in"
            )
        return shas[key][:SHORT_LEN] if kind == "short" else shas[key]

    return TOKEN.sub(replace, text)


def _blob(git: Git, content: str) -> str:
    return git.run("hash-object", "-w", "--stdin", stdin=content.encode("utf-8"))


def _tree(git: Git, entries: dict[str, str]) -> str:
    """Build a tree (recursively) from path -> blob sha."""
    files: dict[str, str] = {}
    subdirs: dict[str, dict[str, str]] = {}
    for path, sha in entries.items():
        head, _, rest = path.partition("/")
        if rest:
            subdirs.setdefault(head, {})[rest] = sha
        else:
            files[head] = sha

    lines = [f"100644 blob {sha}\t{name}" for name, sha in sorted(files.items())]
    for name, children in sorted(subdirs.items()):
        lines.append(f"040000 tree {_tree(git, children)}\t{name}")
    return git.run("mktree", stdin=("\n".join(lines) + "\n").encode("utf-8"))


def build(into: Path) -> Built:
    spec: dict[str, Any] = yaml.safe_load(SCRIPT.read_text(encoding="utf-8"))
    identities = spec["identities"]

    home = into.parent / "fakehome"
    home.mkdir(parents=True, exist_ok=True)
    repo = into
    repo.mkdir(parents=True, exist_ok=True)

    git = Git(repo, home)
    git.run("init", "--bare", "--object-format=sha1", "-b", "main")

    shas: dict[str, str] = {}
    subjects: dict[str, str] = {}
    tree_state: dict[str, str] = {}

    for commit in spec["commits"]:
        key = commit["key"]
        who = identities[commit["author"]]
        date = f"{commit['date']}"

        for path, source in (commit.get("tree") or {}).items():
            if isinstance(source, dict) and "template" in source:
                raw = (HERE / source["template"]).read_text(encoding="utf-8")
                content = _render(raw, shas)
            elif isinstance(source, dict) and "text" in source:
                content = str(source["text"])
            else:
                content = (HERE / str(source)).read_text(encoding="utf-8")
            tree_state[path] = _blob(git, content)

        for path in commit.get("delete") or []:
            tree_state.pop(path, None)

        tree = _tree(git, tree_state)
        parents: list[str] = []
        for parent_key in commit.get("parents") or []:
            parents += ["-p", shas[parent_key]]

        message = str(commit["message"])
        identity = {
            "GIT_AUTHOR_NAME": who["name"], "GIT_AUTHOR_EMAIL": who["email"],
            "GIT_COMMITTER_NAME": who["name"], "GIT_COMMITTER_EMAIL": who["email"],
            "GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date,
        }
        sha = git.run("commit-tree", tree, *parents, "-m", message, env=identity)
        shas[key] = sha
        subjects[key] = message.splitlines()[0]

    for ref, key in spec["refs"].items():
        git.run("update-ref", ref, shas[key])

    return Built(shas=shas, subjects=subjects)


def emit(built: Built, repo: Path, bundle_out: Path, manifest_out: Path) -> None:
    home = repo.parent / "fakehome"
    Git(repo, home).run(
        "bundle", "create", str(bundle_out),
        "--all",
    )
    manifest = {
        key: {"sha": sha, "short": sha[:SHORT_LEN], "subject": built.subjects.get(key, "")}
        for key, sha in built.shas.items()
    }
    manifest_out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="rebuild and verify the committed manifest is unchanged")
    args = parser.parse_args(argv)

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "quest.git"
        built = build(repo)

        if args.check:
            fresh = Path(tmp) / "fresh.json"
            emit(built, repo, Path(tmp) / "fresh.bundle", fresh)
            if not MANIFEST_OUT.exists():
                print("sha_manifest.json is missing — run the build without --check")
                return 1
            if fresh.read_text(encoding="utf-8") != MANIFEST_OUT.read_text(encoding="utf-8"):
                print("the rebuilt history does not match the committed sha_manifest.json.")
                print("Something in history/ changed and reflowed the hashes, which breaks")
                print("every level that quotes one. Commit the new manifest and bundle if")
                print("that was intended.")
                return 1
            print(f"history reproduces exactly ({len(built.shas)} commits)")
            return 0

        emit(built, repo, BUNDLE_OUT, MANIFEST_OUT)
        print(f"wrote {BUNDLE_OUT.name} and {MANIFEST_OUT.name} ({len(built.shas)} commits)")
        for key, sha in built.shas.items():
            print(f"  {sha[:SHORT_LEN]}  {key}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
