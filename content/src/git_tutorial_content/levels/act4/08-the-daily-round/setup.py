"""An ordinary start: one commit waiting, nothing of the student's own yet.

Deliberately the easy shape. A student who has only pulled in 4.4 and 4.5,
where both sides had moved, can come away thinking a merge commit is what
pulling does.
"""

from level_helpers import ALL_BRANCHES, INES, publish, shared_desk

ANCHOR = "tutorial/act4-desk"
ACT4_BRANCHES = ("count-b15", "returns-procedure", "shift-report", "stocktake-plan")
WHEN = "2025-03-28T08:35:00+00:00"

LAST_ENTRY = "- Dispatch note for 3 March started.\n"
WITH_NOTE = "- Dispatch note for 3 March started.\n- Returns procedure started.\n"


def setup(repo, state):
    shared_desk(repo, ANCHOR, branches=ALL_BRANCHES + ACT4_BRANCHES)
    publish(
        repo,
        ANCHOR,
        [(
            "Note the returns procedure",
            INES,
            WHEN,
            {"dispatch/log.md": lambda t: t.replace(LAST_ENTRY, WITH_NOTE)},
        )],
    )
