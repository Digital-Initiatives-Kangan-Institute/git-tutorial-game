"""`wt solve` — the bottom rung of the help ladder.

It runs the level's own `solution.sh`, which is the same artifact CI runs on
every commit. That overlap is the point: the thing a stuck student falls back
on cannot silently rot, because the test suite would fail first.

The script is run whole, in one bash, exactly as the harness runs it. Walking
it statement by statement would execute something subtly different from what
CI proves works — so the explanation is printed first, as a walkthrough, and
then the real thing runs.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from git_tutorial.cli import EXIT_AUTHORING_ERROR, EXIT_OK
from git_tutorial.cli._bind import BindFailure, bind_session
from git_tutorial.session.lifecycle import NoCurrentLevel

# Solution scripts annotate themselves for exactly this: `#:` marks the
# explanation of the statements that follow it.
MARKER = "#:"
MAX_SHOWN = 4


@dataclass(frozen=True)
class Step:
    explanation: str
    commands: tuple[str, ...]


def parse_solution(text: str) -> tuple[Step, ...]:
    """Split a solution script on its `#:` step markers.

    Anything before the first marker is the shebang and `set -euo pipefail`,
    which is plumbing rather than a step worth narrating.
    """
    steps: list[Step] = []
    explanation: str | None = None
    commands: list[str] = []

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(MARKER):
            text = stripped[len(MARKER):].strip()
            # A second `#:` before any command continues the sentence rather
            # than starting a step: long explanations wrap in the source.
            if explanation is not None and not commands:
                explanation = f"{explanation} {text}".strip()
                continue
            if explanation is not None:
                steps.append(Step(explanation, tuple(commands)))
            explanation = text
            commands = []
        elif explanation is not None and stripped and not stripped.startswith("#"):
            commands.append(line.rstrip())

    if explanation is not None:
        steps.append(Step(explanation, tuple(commands)))
    return tuple(steps)


def _print_walkthrough(steps: tuple[Step, ...]) -> None:
    for number, step in enumerate(steps, 1):
        print(f"  {number!s}  {step.explanation}")
        for command in step.commands[:MAX_SHOWN]:
            print(f"       {command.strip()}")
        if len(step.commands) > MAX_SHOWN:
            hidden = len(step.commands) - MAX_SHOWN
            print(f"       {f'... {hidden} more line(s)'}")
        print()


def main(args: argparse.Namespace) -> int:
    try:
        session = bind_session(args)
    except BindFailure as failure:
        print(f"\n  {failure.message}\n")
        return failure.code

    try:
        level = session.current_level()
    except NoCurrentLevel:
        print("\n  You have finished every job; there is nothing left to solve.\n")
        return EXIT_OK

    script = level.directory / (level.solution or "solution.sh")
    if not script.is_file():
        print(f"\n  This level ships no solution script. Expected: {script}\n")
        return EXIT_AUTHORING_ERROR

    steps = parse_solution(script.read_text(encoding="utf-8"))

    print()
    print(f"  {level.title}    {level.label}")
    print()
    print("  Here is the whole level, start to finish.\n")
    _print_walkthrough(steps)

    if not getattr(args, "yes", False):
        print("  Running this does the level for you. Your progress still counts,")
        print("  and the next level starts from here.")
        try:
            reply = input("  Go ahead? [y/N] ").strip().lower()
        except EOFError:
            reply = ""
        if reply not in ("y", "yes"):
            print("\n  Left alone. The Hint button in the browser is still there.\n")
            return EXIT_OK

    print()
    result = _run(script, session.worktree, session.pack.root)
    if result.stdout:
        # Labelled, because otherwise it is an undivided wall of text with
        # nothing saying where the commands stop and git starts answering.
        print(f"  {'what git said:'}\n")
        for line in result.stdout.rstrip().splitlines():
            print(f"    {line}")
        print()

    if result.returncode != 0:
        print(f"  {'The solution script failed.'} "
              "That is a bug in the level, not in what you did.")
        for line in (result.stderr or "").rstrip().splitlines()[-10:]:
            print(f"    {line}")
        print()
        return EXIT_AUTHORING_ERROR

    session.mark_solve_used()

    # Deliberately the real `check`: it grades and records completion exactly
    # as finishing unaided would. The next job still waits for the student.
    from git_tutorial.cli import verbs

    return verbs.check(args)


def _run(script: Path, cwd: Path, pack_root: Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    # Pass the pack on explicitly: a player who used --levels has it nowhere
    # in the environment for the script to inherit.
    env["GITTUTORIAL_LEVELS"] = str(pack_root)
    # The scripts call `gq`, and a player's PATH has it only because play.sh
    # put it there. Running under the interpreter executing us is the one
    # place it is certain to be.
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    # Author dates must stay unset: a student's commits have to vary, so any
    # assertion that accidentally depends on a fixed sha fails loudly.
    for key in ("GIT_AUTHOR_DATE", "GIT_COMMITTER_DATE"):
        env.pop(key, None)

    return subprocess.run(
        ["bash", str(script)],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
