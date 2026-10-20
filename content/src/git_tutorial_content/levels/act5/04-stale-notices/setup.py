"""Four branches went up to Head Office last week, and the student fetched
them all. Since then Ines has deleted three at Head Office.

The student's `origin/*` names for those three are really stale: Head
Office no longer has the branches, and a plain `git fetch` will not
remove the names. Only pruning does. `easter-hours` is still live at
Head Office, so pruning has something to leave alone, and the answer is
not simply "all of them".
"""

from level_helpers import (
    ACT5_BRANCHES,
    ALL_BRANCHES,
    INES,
    MARTA,
    THEO,
    delete_at_head_office,
    publish,
    shared_desk,
)

ANCHOR = "tutorial/act5-desk"

BRANCHES = (
    ("fennick-order", "Draft the Fennick Garden Centre order", THEO,
     "2025-04-01T09:00:00+00:00", "dispatch/fennick-order.md",
     "# Fennick Garden Centre order\n\n- 30 bundles of double-wall cartons\n"),
    ("pallet-audit", "Start the pallet audit", MARTA,
     "2025-04-02T10:30:00+00:00", "stock/pallet-audit.md",
     "# Pallet audit\n\nBays A to C checked. D and E still to do.\n"),
    ("april-returns", "List the April returns", INES,
     "2025-04-03T14:15:00+00:00", "dispatch/april-returns.md",
     "# April returns\n\n- 2 rolls of pallet wrap, split on delivery\n"),
    ("easter-hours", "Propose the Easter opening hours", INES,
     "2025-04-04T08:45:00+00:00", "docs/easter-hours.md",
     "# Easter opening hours\n\nGood Friday and Easter Monday: 08:00 - 12:00.\n"),
)

DELETED = ("fennick-order", "pallet-audit", "april-returns")


def setup(repo, state):
    # The fetch --prune inside shared_desk clears last run's stale names.
    shared_desk(repo, ANCHOR, branches=ALL_BRANCHES + ACT5_BRANCHES)

    for branch, message, author, when, path, text in BRANCHES:
        publish(repo, ANCHOR, [(message, author, when, {path: text})], branch=branch)

    # Last week: the student fetched, and saw all four.
    repo.git("fetch", "origin")

    # Since then: Ines cleared three of them at Head Office.
    delete_at_head_office(repo, *DELETED)
