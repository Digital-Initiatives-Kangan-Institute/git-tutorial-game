"""Ines's branch, at Head Office and nowhere else.

`publish` deletes the local tracking ref, so the student's repository
genuinely does not know the branch exists until they fetch - which is the
only way `git switch returns-procedure` can teach what it teaches.
"""

from level_helpers import ALL_BRANCHES, INES, publish, shared_desk

ANCHOR = "tutorial/act4-desk"
ACT4_BRANCHES = ("count-b15", "returns-procedure", "shift-report", "stocktake-plan")
WHEN = "2025-03-27T15:20:00+00:00"

UNFINISHED = """
## Returns

Returned pallets are booked in against
"""


def setup(repo, state):
    # Deletes the local branch from the last run, and shared_desk clears
    # every branch at Head Office except main.
    shared_desk(repo, ANCHOR, branches=ALL_BRANCHES + ACT4_BRANCHES)
    publish(
        repo,
        ANCHOR,
        [(
            "Start the returns section",
            INES,
            WHEN,
            {"docs/receiving.md": lambda text: text + UNFINISHED},
        )],
        branch="returns-procedure",
    )
