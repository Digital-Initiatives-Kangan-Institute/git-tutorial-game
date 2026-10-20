"""Headless twins of the browser's buttons.

The browser is where the tutorial is played. These exist for the solution
scripts (`wt answer`), for CI (`wt check`), and for anyone working without a
browser. They print plain text: no colour, no layout, nothing to break when
piped.
"""

from __future__ import annotations

import argparse

from git_tutorial.cli import EXIT_ASSERTIONS_FAILED, EXIT_AUTHORING_ERROR, EXIT_OK
from git_tutorial.cli._bind import BindFailure, bind_session
from git_tutorial.errors import TutorialError
from git_tutorial.session.lifecycle import NoCurrentLevel, NotComplete, Session

MAX_ANSWER = 200


def _session(args: argparse.Namespace) -> Session | int:
    try:
        return bind_session(args)
    except BindFailure as failure:
        print(f"\n  {failure.message}\n")
        return failure.code


def answer(args: argparse.Namespace) -> int:
    bound = _session(args)
    if isinstance(bound, int):
        return bound
    try:
        level = bound.current_level()
    except NoCurrentLevel:
        print("\n  There is no job in progress.\n")
        return EXIT_OK

    key = str(args.id)
    slots = bound.answer_slots(level)
    if key not in slots:
        known = ", ".join(slots) or "(this job asks no questions)"
        print(f"\n  This job has no question {key!r}. Its questions: {known}\n")
        return EXIT_ASSERTIONS_FAILED

    value = " ".join(args.value).strip()[:MAX_ANSWER]
    bound.record_answer(key, value)
    print(f"  {key} = {value}")
    return EXIT_OK


def check(args: argparse.Namespace) -> int:
    bound = _session(args)
    if isinstance(bound, int):
        return bound
    try:
        level = bound.current_level()
    except NoCurrentLevel:
        print("\n  You have finished every job.\n")
        return EXIT_OK

    try:
        outcome = bound.check()
    except TutorialError as exc:
        print(f"\n  {exc}\n")
        return EXIT_AUTHORING_ERROR

    report = outcome.report
    ticket = level.job.ticket if level.job else level.id
    print(f"\n  {ticket}  {level.job.title if level.job else level.title}\n")
    for spec, result in zip(level.assertions, report.results, strict=True):
        mark = "x" if result.blocking else ("+" if result.passed else "-")
        label = result.label or str(spec.args.get("label") or result.want)
        print(f"  {mark} {label}")
        if result.blocking:
            print(f"      found: {result.found}")
    print()

    if report.has_authoring_error:
        return EXIT_AUTHORING_ERROR
    if bound.phase() != "working":
        print("  Job complete." + ("" if bound.phase() == "finished" else
                                    "  `wt next` (or the browser) starts the next one."))
        print()
        return EXIT_OK
    return EXIT_ASSERTIONS_FAILED


def next_job(args: argparse.Namespace) -> int:
    bound = _session(args)
    if isinstance(bound, int):
        return bound
    if bound.probe.locked() is not None:
        print("\n  git is busy in your workspace. Try again in a moment.\n")
        return EXIT_ASSERTIONS_FAILED
    try:
        started = bound.begin_next()
    except NotComplete as exc:
        print(f"\n  {exc}.\n")
        return EXIT_ASSERTIONS_FAILED
    except NoCurrentLevel:
        print("\n  There is no job in progress.\n")
        return EXIT_OK
    if started is None:
        print("\n  That was the last job. Well done.\n")
        return EXIT_OK
    level = bound.pack.load(started)
    print(f"\n  Started {level.job.ticket if level.job else level.id}: {level.title}\n")
    return EXIT_OK


def reset(args: argparse.Namespace) -> int:
    bound = _session(args)
    if isinstance(bound, int):
        return bound
    try:
        level = bound.current_level()
    except NoCurrentLevel:
        print("\n  There is no job in progress.\n")
        return EXIT_OK

    if not getattr(args, "yes", False):
        print(f"\n  This puts the workspace back to the start of {level.title}.")
        print("  Uncommitted changes in it will be lost.")
        try:
            reply = input("  Go ahead? [y/N] ").strip().lower()
        except EOFError:
            reply = ""
        if reply not in ("y", "yes"):
            print("\n  Left alone.\n")
            return EXIT_OK

    bound.reset_current()
    print(f"\n  {level.title} is back at its start.\n")
    return EXIT_OK
