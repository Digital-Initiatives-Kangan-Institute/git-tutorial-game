"""Everything the browser shows, as one JSON-ready dict.

The page holds no git or game logic of its own: it draws this. Built by the
engine thread from the same snapshot it just graded, so the job sheet and
the warehouse picture can never disagree.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from git_tutorial.checker import CheckReport
from git_tutorial.content import prose
from git_tutorial.git.snapshot import RepoSnapshot
from git_tutorial.git.supplier import HeadOffice
from git_tutorial.levels.model import Level
from git_tutorial.scene.warehouse import Move
from git_tutorial.session.lifecycle import YARD_HIDDEN, Session
from git_tutorial.state.models import Progress
from git_tutorial.web.picture import picture


def build(
    session: Session,
    *,
    level: Level | None,
    report: CheckReport | None,
    snapshot: RepoSnapshot | None,
    move: Move | None,
    unseen: int | None,
    events: Sequence[dict[str, Any]],
    office: HeadOffice | None = None,
    remembered: frozenset[str] | None = None,
    seq: int,
    error: str | None = None,
) -> dict[str, Any]:
    progress = session.progress
    phase = session.phase(progress)
    state: dict[str, Any] = {
        "seq": seq,
        "error": error,
        "phase": phase,
        "course": _course(session, level),
        "level": None,
        "goals": [],
        "hints": {"shown": [], "total": 0, "more": False},
        "success": None,
        "warehouse": None if snapshot is None else picture(
            snapshot, unseen=unseen, hidden=_hidden(progress, level), office=office,
            remembered=remembered, worktree=session.worktree, git_dir=session.probe.git_dir,
        ),
        "move": _move(move),
        "events": list(events),
    }
    if level is None:
        return state

    entry = progress.for_level(level.id)
    ctx = prose.SubstitutionContext(shas=session.pack.shas(), snapshot=snapshot, level=level)
    state["level"] = {
        "id": level.id,
        "act": level.act,
        "number": level.level,
        "title": level.title,
        "label": level.label,
        "job": None if level.job is None else {
            "ticket": level.job.ticket, "from": level.job.sender, "title": level.job.title,
        },
        "teaches": list(level.teaches),
        "intro": prose.blocks_for(level, "intro", ctx),
        "brief": prose.blocks_for(level, "brief", ctx),
    }
    if report is not None:
        answers = session.merged_answers(level, entry)
        state["goals"] = _goals(level, report, answers)
    state["hints"] = {
        "shown": [
            {"rung": index + 1, "text": level.hints[index].text,
             "blocks": _hint_blocks(level.hints[index].text, ctx)}
            for index in entry.hints_shown if index < len(level.hints)
        ],
        "total": len(level.hints),
        "more": len(entry.hints_shown) < len(level.hints),
    }
    if phase != "working":
        state["success"] = {
            "blocks": prose.blocks_for(level, "success", ctx),
            "learned": list(level.teaches),
            "last": phase == "finished",
        }
    return state


def _hidden(progress: Progress, level: Level | None) -> frozenset[str]:
    if level is None:
        return frozenset()
    return frozenset(progress.for_level(level.id).extra.get(YARD_HIDDEN, ()))


def _hint_blocks(text: str, ctx: prose.SubstitutionContext) -> list[dict[str, Any]]:
    try:
        return prose.to_blocks(prose.parse_prose(prose.substitute(text, ctx, strict=False)))
    except Exception:
        return [{"type": "pre", "lines": text.splitlines()}]


def _course(session: Session, current: Level | None) -> list[dict[str, Any]]:
    progress = session.progress
    out: list[dict[str, Any]] = []
    for act in session.pack.acts:
        levels = []
        for number, level_id in enumerate(act.level_ids, 1):
            if level_id in progress.completed:
                status = "done"
            elif current is not None and level_id == current.id:
                status = "current"
            else:
                status = "locked"
            levels.append({"id": level_id, "number": number,
                           "title": _title(session, level_id), "status": status})
        out.append({"act": act.act, "title": act.title, "subject": act.subject,
                    "levels": levels})
    return out


def _title(session: Session, level_id: str) -> str:
    try:
        return session.pack.load(level_id).title
    except Exception:
        return level_id


def _goals(
    level: Level, report: CheckReport, answers: dict[str, str]
) -> list[dict[str, Any]]:
    """The job sheet. Results line up with the level's assertions by position."""
    goals: list[dict[str, Any]] = []
    for index, (spec, result) in enumerate(zip(level.assertions, report.results, strict=True)):
        answer = None
        if spec.kind == "answer":
            key = str(spec.args.get("id", ""))
            answer = {
                "id": key,
                "prompt": str(spec.args.get("prompt", key)),
                "input": "sha" if "equals_commit" in spec.args
                else str(spec.args.get("input", "text")),
                "value": answers.get(key, ""),
            }
        goals.append({
            "index": index,
            "kind": spec.kind,
            "label": str(spec.args.get("label") or result.want),
            "story": str(spec.args.get("story", "")),
            "passed": result.passed,
            "blocking": result.blocking,
            "advisory": not result.enforced,
            "want": result.want,
            "found": result.found,
            "error": result.error,
            "answer": answer,
        })
    return goals


def _move(move: Move | None) -> dict[str, str] | None:
    if move is None:
        return None
    return {"command": move.command, "source": move.source, "dest": move.dest,
            "detail": move.detail}
