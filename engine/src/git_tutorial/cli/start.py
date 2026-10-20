from __future__ import annotations

import argparse
import hashlib
import os
import shutil
from pathlib import Path

from git_tutorial.cli import EXIT_AUTHORING_ERROR, EXIT_OK
from git_tutorial.errors import TutorialError
from git_tutorial.git.runner import GitRunner
from git_tutorial.levels.pack import LevelPack, discover_pack
from git_tutorial.session.lifecycle import Session
from git_tutorial.state import paths
from git_tutorial.state.store import StateStore
from git_tutorial.testing.builder import RepoBuilder

STAMP = "gittutorial-bundle.stamp"


def main(args: argparse.Namespace) -> int:
    try:
        pack = discover_pack(getattr(args, "levels", None))
    except TutorialError as exc:
        print(f"\n{exc}\n")
        return EXIT_AUTHORING_ERROR

    paths.ensure_home()

    try:
        archive = _provision_archive(pack, fresh=bool(getattr(args, "fresh", False)))
        dest = _provision_clone(pack, archive, args)
    except TutorialError as exc:
        print(f"\n  {exc}\n")
        return EXIT_AUTHORING_ERROR

    session = Session.open(repo_path=dest, levels=getattr(args, "levels", None))
    store = StateStore(session.worktree)
    progress = store.load()

    if progress.started:
        return _resume(session, dest)

    with store.mutate() as fresh_progress:
        fresh_progress.pack_id = pack.pack_id
        fresh_progress.pack_version = pack.pack_version
        fresh_progress.repo_path = str(session.worktree)

    level_id = getattr(args, "level", None) or pack.first_level_id()
    try:
        session.begin_level(level_id)
    except TutorialError as exc:
        print(f"\n  The first job could not be set up: {exc}\n")
        return EXIT_AUTHORING_ERROR

    print("\n  Your workspace is ready: a copy of Tallowmere Distribution's records.")
    _print_location(dest)
    return EXIT_OK


def _resume(session: Session, dest: Path) -> int:
    try:
        title = session.current_level().title
    except TutorialError:
        title = "the end of the course"
    print(f"\n  Welcome back. You are on: {title}")
    _print_location(dest)
    return EXIT_OK


def _print_location(dest: Path) -> None:
    # play.sh already puts the student inside the workspace, so telling them
    # to cd somewhere they are standing would only be confusing.
    if os.environ.get("GIT_TUTORIAL_ACTIVE"):
        return
    print(f"  workspace   {dest}")
    print(f"  next        cd {dest}  then run  wt")
    print()


def _provision_archive(pack: LevelPack, *, fresh: bool) -> Path:
    archive = paths.head_office_dir()
    bundle = pack.bundle_path()
    if bundle is None:
        raise TutorialError(
            f"the level pack at {pack.root} has no depot.bundle — it cannot start a workspace"
        )

    stamp = hashlib.sha256(bundle.read_bytes()).hexdigest() + f":{pack.pack_version}"

    if fresh and archive.exists():
        shutil.rmtree(archive)

    if archive.exists():
        existing = (archive / STAMP).read_text(encoding="utf-8").strip() \
            if (archive / STAMP).exists() else ""
        if existing == stamp:
            return archive
        _fetch_bundle(archive, bundle)
        (archive / STAMP).write_text(stamp, encoding="utf-8")
        return archive

    archive.mkdir(parents=True, exist_ok=True)
    bare = GitRunner(archive)
    bare.run("init", "--bare", "--object-format=sha1", "-b", "main")

    # `bundle verify` needs a repository to resolve prerequisites against, so
    # it runs after init and before anything depends on the objects.
    verify = bare.run("bundle", "verify", str(bundle), check=False)
    if not verify.ok:
        shutil.rmtree(archive, ignore_errors=True)
        raise TutorialError(
            "the level pack's practice history is damaged and cannot be unpacked.\n"
            f"  {verify.stderr.strip()}\n"
            "  Re-install the pack, or `git pull` it if you cloned it."
        )

    _fetch_bundle(archive, bundle)
    bare.run("symbolic-ref", "HEAD", "refs/heads/main")
    # Act 4 asks the student to force-push; Head Office has to accept it.
    bare.run("config", "receive.denyNonFastForwards", "false")
    bare.run("config", "gc.auto", "0")
    (archive / STAMP).write_text(stamp, encoding="utf-8")
    return archive


def _fetch_bundle(archive: Path, bundle: Path) -> None:
    # --prune, because the archive is shared and long-lived. Without it a ref
    # from a pack the player installed months ago survives forever and is
    # cloned into every new workspace: a renamed anchor left nine commits of
    # retired content in the repository, visible in every `log --graph --all`
    # the student ran and explained by nothing.
    GitRunner(archive).run(
        "fetch", "--prune", "--prune-tags", str(bundle),
        "+refs/heads/*:refs/heads/*",
        "+refs/tutorial/*:refs/tutorial/*",
        "+refs/tags/*:refs/tags/*",
    )


def _provision_clone(pack: LevelPack, archive: Path, args: argparse.Namespace) -> Path:
    name = getattr(args, "dir", None) or pack.workspace_dir_name
    dest = (Path.cwd() / name).resolve()

    if getattr(args, "reclone", False) and dest.exists():
        shutil.rmtree(dest)

    if dest.exists():
        if not (dest / ".git").exists():
            raise TutorialError(
                f"{dest} already exists and is not a git repository.\n"
                "  Move it aside, or choose another name with --dir."
            )
        origin = GitRunner(dest).run(
            "config", "--get", "remote.origin.url", check=False
        ).stdout.strip()
        if Path(origin or "x").resolve() != archive.resolve():
            raise TutorialError(
                f"{dest} is a git repository, but not this tutorial's workspace.\n"
                "  Choose another name with --dir."
            )
    else:
        GitRunner(Path.cwd()).run("clone", str(archive), str(dest))

    _configure_clone(dest)
    return dest


def _configure_clone(dest: Path) -> None:
    runner = GitRunner(dest)

    # Unset-then-add is the only genuinely idempotent way to set a multi-value
    # config key. Tutorial refs are not fetched by a plain clone.
    runner.run("config", "--unset-all", "remote.origin.fetch", check=False)
    runner.run("config", "--add", "remote.origin.fetch", "+refs/heads/*:refs/remotes/origin/*")
    runner.run("config", "--add", "remote.origin.fetch", "+refs/tutorial/*:refs/tutorial/*")
    runner.run("fetch", "origin", check=False)

    # Act 3 asserts over commits made unreachable by `reset --hard`. A
    # background gc during a five-day gap would delete them for real.
    runner.run("config", "gc.auto", "0")
    runner.run("config", "gc.pruneExpire", "never")

    # Since git 2.27, `git pull` on diverged branches refuses to run until
    # the repository says whether to merge or rebase. Act 4 is built on pull
    # meaning fetch-then-merge, and a student who types the command the
    # level just taught them should not get a fatal error and twelve lines
    # of hint. Merge is also the choice this game can defend: it is what
    # 4.4 explains, and rebase is on the recognise-only list. 4.4's prose
    # shows the message and says how to make the same choice elsewhere.
    runner.run("config", "pull.rebase", "false")

    if not runner.run("config", "--get", "user.email", check=False).stdout.strip():
        runner.run("config", "user.name", "Trainee")
        runner.run("config", "user.email", "trainee@git-tutorial.invalid")
        print("  note: git had no author name set, so this repo uses a placeholder.")
        print("        set your own with: git config --global user.name \"Your Name\"")


def repo_handle(dest: Path) -> RepoBuilder:
    return RepoBuilder(dest, deterministic=False)
