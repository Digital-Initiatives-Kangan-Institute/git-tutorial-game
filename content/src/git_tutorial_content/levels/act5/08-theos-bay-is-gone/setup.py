"""Theo counted aisle C on a branch and sent it up; the student fetched and
saw `origin/aisle-c-count`. Since then Ines merged it into main at Head
Office and deleted the branch there.

So the student's `origin/aisle-c-count` is a really stale name, and their
`main` and `origin/main` are really behind Head Office's merge. A plain
`git pull` brings the merge but leaves the stale name; only pruning takes
it down, and pulling is what shows Theo's work was folded in, not lost.
"""

from level_helpers import (
    ACT5_BRANCHES,
    ALL_BRANCHES,
    INES,
    THEO,
    delete_at_head_office,
    merge_at_head_office,
    publish,
    shared_desk,
)

ANCHOR = "tutorial/act5-desk"
WHEN_COUNT = "2025-04-15T07:50:00+00:00"
WHEN_MERGE = "2025-04-15T11:30:00+00:00"

AISLE_C = """# Aisle C stock

**C-03 Garden twine, jute**

18 spools on the shelf.

**C-04 Seed trays, 40 cell**

6 boxes of 50.
"""


def setup(repo, state):
    # The fetch --prune inside shared_desk clears last run's stale name.
    shared_desk(repo, ANCHOR, branches=ALL_BRANCHES + ACT5_BRANCHES)

    publish(
        repo, ANCHOR,
        [("Count aisle C", THEO, WHEN_COUNT, {"stock/aisle-c.md": AISLE_C})],
        branch="aisle-c-count",
    )
    # The student fetched while Theo's branch was live.
    repo.git("fetch", "origin")

    # Then, at Head Office: Ines merged it and took the branch down.
    merge_at_head_office(
        repo, ANCHOR, "origin/aisle-c-count",
        message="Merge Theo's aisle C count", author=INES, date=WHEN_MERGE,
    )
    delete_at_head_office(repo, "aisle-c-count")
