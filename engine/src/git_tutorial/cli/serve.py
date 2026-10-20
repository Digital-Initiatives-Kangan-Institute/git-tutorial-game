"""Bare `wt`: the watcher and the web server, in one process.

The terminal it runs in is deliberately quiet - the story, the job sheet and
the warehouse are in the browser. Here: the address, and one line when
something worth knowing happens, so a student who closed the tab can tell
the watcher is still alive.
"""

from __future__ import annotations

import argparse
import threading
import time
import webbrowser
from typing import Any

from git_tutorial.cli import EXIT_OK
from git_tutorial.cli._bind import BindFailure, bind_session
from git_tutorial.web.engine import Engine
from git_tutorial.web.server import Server, serve

DEFAULT_PORT = 7171


def main(args: argparse.Namespace) -> int:
    try:
        session = bind_session(args)
    except BindFailure as failure:
        print(f"\n  {failure.message}\n")
        return failure.code

    engine = Engine(session)
    engine.step()

    server = _open(engine, getattr(args, "port", None))
    stop = threading.Event()
    threading.Thread(target=engine.run, args=(stop,), daemon=True, name="wt-engine").start()
    threading.Thread(target=_log, args=(engine, stop), daemon=True, name="wt-log").start()

    print()
    print("  git-tutorial is watching your workspace.")
    print(f"    workspace  {session.worktree}")
    print(f"    open       {server.url}")
    print()
    print("  Keep this window open. Work in another terminal; ctrl-c here stops it.")
    print(flush=True)
    if not getattr(args, "no_browser", False):
        webbrowser.open(server.url)

    try:
        server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        server.server_close()
    print("\n  Stopped watching. Your progress is saved; run `wt` to carry on.\n")
    return EXIT_OK


def _open(engine: Engine, port: int | None) -> Server:
    if port is not None:
        return serve(engine, port=port)
    try:
        return serve(engine, port=DEFAULT_PORT)
    except OSError:
        return serve(engine, port=0)  # the usual port is taken; any free one will do


def _log(engine: Engine, stop: threading.Event) -> None:
    seen = 0
    error: str | None = None
    while not stop.is_set():
        state = engine.wait(engine.current["seq"], timeout=5.0)
        for event in state.get("events", []):
            if event["id"] > seen:
                seen = event["id"]
                line = _describe(event, state)
                if line:
                    print(f"  {time.strftime('%H:%M')}  {line}", flush=True)
        if state.get("error") != error:
            error = state.get("error")
            if error:
                print(f"  {time.strftime('%H:%M')}  problem reading the workspace: {error}",
                      flush=True)


def _describe(event: dict[str, Any], state: dict[str, Any]) -> str | None:
    level = state.get("level") or {}
    job = (level.get("job") or {}).get("ticket") or level.get("id", "")
    kind = event["kind"]
    if kind == "level_complete":
        return f"{job} complete" + ("" if event.get("last") else
                                    " - start the next job from the browser")
    if kind == "level_arrived":
        return f"new job: {job} {level.get('title', '')}"
    if kind == "level_reset":
        return f"{job} reset to its start"
    if kind == "hint" and not event.get("asked"):
        return f"a hint is waiting on the job sheet (hint {event.get('rung')})"
    return None
