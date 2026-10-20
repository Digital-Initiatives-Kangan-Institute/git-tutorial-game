"""`wt` — the warehouse tutorial's one command.

Bare `wt` is the watcher: it grades the student's repository and serves the
browser view from the same process. Everything else is either setup
(`start`, `doctor`) or a headless twin of a browser button, for solution
scripts, CI and anyone without a browser (`answer`, `check`, `next`, `reset`).
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from git_tutorial.version import __version__

# Part of the contract: CI and the level harness branch on these.
EXIT_OK = 0
EXIT_ASSERTIONS_FAILED = 1
EXIT_AUTHORING_ERROR = 2
EXIT_NO_REPO = 3


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wt", description="git-tutorial: learn git by running a warehouse"
    )
    parser.add_argument("--version", action="version", version=f"git-tutorial {__version__}")
    parser.add_argument("--repo", help="path to the workspace repo (default: cwd)")
    parser.add_argument("--levels", help="path to a level pack")
    parser.add_argument("--debug", action="store_true", help="show tracebacks")
    parser.add_argument("--port", type=int, help="serve on this port (default 7171)")
    parser.add_argument("--no-browser", action="store_true", help="print the address only")

    sub = parser.add_subparsers(dest="command")

    sub.add_parser("doctor", help="check that this machine can run the tutorial")

    start = sub.add_parser("start", help="create or resume your workspace")
    start.add_argument("--dir", help="name for the workspace directory")
    start.add_argument("--level", help="begin at this level id")
    start.add_argument("--fresh", action="store_true", help="rebuild Head Office from the bundle")
    start.add_argument("--reclone", action="store_true", help="delete and re-clone the workspace")

    answer = sub.add_parser("answer", help="answer a question on the current job sheet")
    answer.add_argument("id", help="the question id, as shown on the job sheet")
    answer.add_argument("value", nargs="+", help="your answer")

    sub.add_parser("check", help="grade the current job once and print the job sheet")
    sub.add_parser("next", help="start the next job (the current one must be complete)")

    reset = sub.add_parser("reset", help="restart the current job")
    reset.add_argument("--yes", action="store_true", help="skip the confirmation")

    solve = sub.add_parser("solve", help="do the current job for you, explaining each step")
    solve.add_argument("--yes", action="store_true", help="skip the confirmation")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        return _dispatch(args)
    except KeyboardInterrupt:
        print()
        return EXIT_OK
    except Exception:
        if args.debug:
            raise
        import traceback

        print(f"\n  something went wrong: {traceback.format_exc(limit=0).strip()}")
        print("  run again with --debug for the full traceback\n")
        return EXIT_AUTHORING_ERROR


def _dispatch(args: argparse.Namespace) -> int:
    if args.command is None:
        from git_tutorial.cli import serve

        return serve.main(args)
    if args.command == "doctor":
        from git_tutorial.cli import doctor

        return doctor.main(args)
    if args.command == "start":
        from git_tutorial.cli import start

        return start.main(args)
    if args.command == "solve":
        from git_tutorial.cli import solve

        return solve.main(args)

    from git_tutorial.cli import verbs

    handlers = {
        "answer": verbs.answer,
        "check": verbs.check,
        "next": verbs.next_job,
        "reset": verbs.reset,
    }
    return handlers[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
