"""A pull stopped in a conflict, and a rush job that cannot wait.

The student committed their B-15 count; Theo sent a different one to
Head Office. The student pulled, and the pull genuinely stopped with
stock/aisle-b.md conflicted: setup runs that pull, so the job opens in
the middle of a paused merge. Beside it is the half-written dispatch
note for a rush order, not yet committed.

The note has to be committed on its own, before the stock count is
settled, and a commit made now would finish the merge instead. So the
way through is `git merge --abort`, commit the rush note, then pull
again and resolve properly. The goals check that order: the merge
commit's first parent already holds the finished note.
"""

from level_helpers import (
    ACT5_BRANCHES,
    ACT6_BRANCHES,
    ALL_BRANCHES,
    THEO,
    diverge_from_head_office,
    shared_desk,
)

ANCHOR = "tutorial/act6-desk"
WHEN_THEO = "2026-03-26T12:50:00+00:00"
WHEN_MINE = "2026-03-26T13:05:00+00:00"

B15 = "Not counted yet.\n"

RUSH = "dispatch/2026-03-26.md"
RUSH_NOTE = """# Dispatch note: 26 March

Rush order for Fennick Garden Centre: two pallets of double wall
cartons, wrapped and labelled, collected at
"""


def setup(repo, state):
    # shared_desk aborts the paused merge a previous run left behind.
    shared_desk(repo, ANCHOR, branches=ALL_BRANCHES + ACT5_BRANCHES + ACT6_BRANCHES)

    diverge_from_head_office(
        repo,
        ANCHOR,
        theirs=[(
            "Count B-15 for the stocktake", THEO, WHEN_THEO,
            {"stock/aisle-b.md": lambda t: t.replace(B15, "24 bundles counted.\n")},
        )],
        ours=[(
            "Record my B-15 count", None, WHEN_MINE,
            {"stock/aisle-b.md": lambda t: t.replace(B15, "22 bundles counted.\n")},
        )],
    )

    # The pull the student had just started when the phone rang. It stops.
    repo.git("-c", "pull.rebase=false", "pull", "--no-edit", check=False)

    # And the rush job, half written, never committed.
    repo.write_file(RUSH, RUSH_NOTE)
