"""Two people counted bin B-14 on the same morning.

Theo sent his figure up to Head Office; the student committed theirs
locally without pulling first. Both changed the same line of
stock/aisle-b.md, so the student's `git pull` stops with a real
"both changed" conflict. Marta's own recount settles it.
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
WHEN_THEO = "2026-03-23T08:40:00+00:00"
WHEN_MINE = "2026-03-23T09:10:00+00:00"

ORIGINAL = "40 rolls on the shelf.\n"
THEO_SAYS = "37 rolls counted for the stocktake.\n"
MINE_SAYS = "39 rolls counted for the stocktake.\n"


def setup(repo, state):
    # shared_desk abandons last run's paused merge before anything else.
    shared_desk(repo, ANCHOR, branches=ALL_BRANCHES + ACT5_BRANCHES + ACT6_BRANCHES)

    diverge_from_head_office(
        repo,
        ANCHOR,
        theirs=[(
            "Count B-14 for the stocktake",
            THEO,
            WHEN_THEO,
            {"stock/aisle-b.md": lambda t: t.replace(ORIGINAL, THEO_SAYS)},
        )],
        ours=[(
            "Record my B-14 count",
            None,
            WHEN_MINE,
            {"stock/aisle-b.md": lambda t: t.replace(ORIGINAL, MINE_SAYS)},
        )],
    )
