"""What origin actually holds, as opposed to what this clone last heard.

`origin/main` is only a record of the remote as of the last fetch, and the
gap between the two is the idea Act 4 is hardest on. The tutorial's origin (Head Office) is
a bare repository on the same disk (`~/.gittutorial/head-office.git`), so the gap
can be measured without the network: read-only, and only for a local path.
Anything else — a URL, a missing directory, a rewritten history — yields
None, which the warehouse view draws as "unknown" by drawing nothing.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from git_tutorial.errors import TutorialError
from git_tutorial.git.runner import GitRunner
from git_tutorial.git.snapshot import RepoSnapshot


def unseen(runner: GitRunner, snapshot: RepoSnapshot) -> int | None:
    """Commits on the upstream branch at origin that have not been fetched."""
    if not snapshot.head_ref:
        return None
    upstream = snapshot.upstream.get(snapshot.head_ref)
    if not upstream:
        return None
    remote, _, branch = upstream.partition("/")
    try:
        url = runner.run("config", "--get", f"remote.{remote}.url", check=False).stdout.strip()
        there = _local(runner.cwd, url)
        if there is None:
            return None
        other = GitRunner(there, timeout=2.0)
        tip = other.run("rev-parse", "--verify", "-q", f"refs/heads/{branch}^{{commit}}",
                        check=False)
        if not tip.ok:
            return None
        known = snapshot.remote_refs.get(upstream)
        if tip.stdout.strip() == known:
            return 0
        exclude = [f"^{known}"] if known else []
        count = other.run("rev-list", "--count", tip.stdout.strip(), *exclude, check=False)
        return int(count.stdout.strip()) if count.ok else None
    except (TutorialError, OSError, subprocess.SubprocessError, ValueError):
        return None


@dataclass(frozen=True, slots=True)
class HeadOffice:
    """What origin really holds right now: branch and tag tips (tags peeled
    to the commit they seal)."""

    branches: dict[str, str]
    tags: dict[str, str]


def head_office_dir(runner: GitRunner, remote: str = "origin") -> Path | None:
    url = runner.run("config", "--get", f"remote.{remote}.url", check=False).stdout.strip()
    return _local(runner.cwd, url)


def head_office(runner: GitRunner, remote: str = "origin") -> HeadOffice | None:
    """None when origin is not a repository on this disk."""
    try:
        there = head_office_dir(runner, remote)
        if there is None:
            return None
        listed = GitRunner(there, timeout=5.0).run(
            "for-each-ref", "--format=%(refname)%09%(objectname)%09%(*objectname)",
            "refs/heads", "refs/tags", check=False,
        )
    except (TutorialError, OSError, subprocess.SubprocessError):
        return None
    if not listed.ok:
        return None
    branches: dict[str, str] = {}
    tags: dict[str, str] = {}
    for line in listed.stdout.splitlines():
        name, _, rest = line.partition("\t")
        sha, _, peeled = rest.partition("\t")
        if name.startswith("refs/heads/"):
            branches[name[len("refs/heads/"):]] = sha
        elif name.startswith("refs/tags/"):
            tags[name[len("refs/tags/"):]] = peeled or sha
    return HeadOffice(branches=branches, tags=tags)


def remote_commits(runner: GitRunner, remote: str = "origin") -> set[str]:
    """Every commit the remote's branches reach, when it is on this disk.

    Empty for anything this cannot read: the set is only ever used to hide
    things, so not knowing must mean hiding nothing.
    """
    try:
        there = head_office_dir(runner, remote)
        if there is None:
            return set()
        listed = GitRunner(there, timeout=5.0).run("rev-list", "--branches", check=False)
        return set(listed.stdout.split()) if listed.ok else set()
    except (TutorialError, OSError, subprocess.SubprocessError):
        return set()


def _local(cwd: Path, url: str) -> Path | None:
    if not url:
        return None
    if url.startswith("file://"):
        url = url[len("file://"):]
    elif "://" in url or (":" in url and not Path(url).drive):
        return None  # ssh, https, or scp-style host:path
    path = Path(url)
    if not path.is_absolute():
        path = cwd / path
    return path if path.is_dir() else None
