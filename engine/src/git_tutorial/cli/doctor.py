from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from git_tutorial import portable
from git_tutorial.errors import TutorialError
from git_tutorial.git.discovery import discover
from git_tutorial.git.runner import GitRunner

Status = Literal["ok", "warn", "fail"]

MIN_PYTHON = (3, 11)
MIN_GIT = (2, 23)  # `switch` and `restore`
PREFERRED_GIT = (2, 25)


@dataclass(frozen=True, slots=True)
class Check:
    name: str
    status: Status
    found: str
    remedy: str = ""


def _version_tuple(text: str) -> tuple[int, ...]:
    parts: list[int] = []
    for chunk in text.split("."):
        digits = "".join(c for c in chunk if c.isdigit())
        if not digits:
            break
        parts.append(int(digits))
    return tuple(parts)


def check_python() -> Check:
    found = ".".join(str(n) for n in sys.version_info[:3])
    if sys.version_info[:2] < MIN_PYTHON:
        needed = f"{MIN_PYTHON[0]}.{MIN_PYTHON[1]}"
        return Check("python", "fail", found, f"git-tutorial needs Python {needed} or newer")
    return Check("python", "ok", found)


def check_git() -> tuple[Check, tuple[int, ...] | None]:
    binary = shutil.which("git")
    if binary is None:
        return Check("git", "fail", "not found", "install git, then reopen your terminal"), None
    try:
        raw = subprocess.run(
            [binary, "--version"], capture_output=True, text=True, timeout=10, check=True
        ).stdout.strip()
    except (subprocess.SubprocessError, OSError):
        return Check("git", "fail", "could not run `git --version`", "check your git install"), None

    version = _version_tuple(raw.removeprefix("git version "))
    if version < MIN_GIT:
        return (
            Check("git", "fail", raw, "git 2.23+ is required for `switch` and `restore`"),
            version,
        )
    if version < PREFERRED_GIT:
        return Check("git", "warn", raw, "git 2.25+ is recommended"), version
    return Check("git", "ok", raw), version


def check_on_path() -> Check:
    # A student running the single-file build has no `wt` to find and does
    # not want one: telling them to reinstall with pipx would be advice
    # about a problem they have deliberately avoided having.
    archive = portable.archive_path()
    if archive is not None:
        return Check("running from", "ok", str(archive))

    found = shutil.which("wt")
    if found is None:
        return Check(
            "wt on PATH",
            "warn",
            "not found",
            "reinstall with pipx, or run the tutorial as `python -m git_tutorial`",
        )
    return Check("wt on PATH", "ok", found)


def check_identity() -> Check:
    """git refuses to commit without these, which blocks the second job outright."""
    runner = GitRunner(Path.cwd())
    name = runner.run("config", "--get", "user.name", check=False).stdout.strip()
    email = runner.run("config", "--get", "user.email", check=False).stdout.strip()
    if name and email:
        return Check("git identity", "ok", f"{name} <{email}>")
    return Check(
        "git identity",
        "fail",
        "not configured",
        'run: git config --global user.name "Your Name" '
        '&& git config --global user.email "you@example.com"',
    )


def check_home() -> Check:
    home = Path(os.environ.get("GITTUTORIAL_HOME", Path.home() / ".gittutorial"))
    try:
        home.mkdir(parents=True, exist_ok=True)
        probe = home / ".write-probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except OSError as exc:
        return Check(
            "state directory",
            "fail",
            f"{home}: {exc}",
            "check permissions on your home directory",
        )
    return Check("state directory", "ok", str(home))


def check_terminal() -> Check:
    encoding = (sys.stdout.encoding or "unknown").lower()
    if not sys.stdout.isatty():
        return Check("terminal", "warn", "not a tty", "run git-tutorial in an interactive terminal")
    if encoding in ("cp1252", "ascii", "unknown"):
        return Check(
            "terminal",
            "warn",
            f"encoding {encoding}",
            "git output may mangle some characters; Windows Terminal or Git Bash is recommended",
        )
    return Check("terminal", "ok", f"encoding {encoding}")


def check_bash() -> Check:
    """`wt solve` runs each level's solution.sh, so bash is not optional."""
    found = shutil.which("bash")
    if found is None:
        return Check(
            "bash",
            "fail",
            "not found",
            "install Git Bash (Windows) or bash; `wt solve` cannot run without it",
        )
    return Check("bash", "ok", found)


def check_autocrlf() -> Check:
    if sys.platform != "win32":
        return Check("core.autocrlf", "ok", "not applicable")
    runner = GitRunner(Path.cwd())
    value = runner.run("config", "--get", "core.autocrlf", check=False).stdout.strip()
    if value.lower() == "true":
        return Check(
            "core.autocrlf",
            "warn",
            "true",
            "run: git config --global core.autocrlf input — `true` rewrites line endings "
            "and can make file comparisons fail",
        )
    return Check("core.autocrlf", "ok", value or "unset")


def check_repo() -> Check:
    try:
        location = discover(Path.cwd())
    except TutorialError:
        return Check(
            "workspace",
            "warn",
            "not inside a git repository",
            "run `wt start` to set one up, then cd into it",
        )
    return Check("workspace", "ok", str(location.worktree))


def run_checks() -> list[Check]:
    git_check, _version = check_git()
    return [
        check_python(),
        git_check,
        check_on_path(),
        check_identity(),
        check_bash(),
        check_home(),
        check_terminal(),
        check_autocrlf(),
        check_repo(),
    ]


_GLYPH: dict[Status, str] = {"ok": "ok  ", "warn": "warn", "fail": "FAIL"}


def render(checks: list[Check]) -> str:
    width = max(len(c.name) for c in checks)
    lines = ["", "  git-tutorial doctor", ""]
    for check in checks:
        lines.append(f"  {_GLYPH[check.status]}  {check.name.ljust(width)}   {check.found}")
        if check.remedy:
            lines.append(f"        {' ' * width}   -> {check.remedy}")
    failures = sum(1 for c in checks if c.status == "fail")
    lines.append("")
    lines.append("  all good" if failures == 0 else f"  {failures} blocking problem(s) above")
    lines.append("")
    return "\n".join(lines)


def main(_args: object = None) -> int:
    checks = run_checks()
    print(render(checks))
    return 1 if any(c.status == "fail" for c in checks) else 0
