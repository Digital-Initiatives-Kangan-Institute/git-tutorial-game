"""The student deleted a sheet that Head Office has just updated.

The student, thinking the scanner's BOOK-IN screens had replaced it,
deleted docs/receiving.md and committed. Ines, at Head Office, updated
the same sheet with a step for chilled loads. The pull stops with the
mirror image of 6.5: "deleted in HEAD and modified in <theirs>", shown
as "deleted by us".

Ines's sheet is current procedure, so the answer is her version whole:
`git restore --theirs`, then add.
"""

from level_helpers import (
    ACT5_BRANCHES,
    ACT6_BRANCHES,
    ALL_BRANCHES,
    INES,
    diverge_from_head_office,
    shared_desk,
)

ANCHOR = "tutorial/act6-desk"
WHEN_INES = "2026-03-26T15:40:00+00:00"
WHEN_MINE = "2026-03-27T07:15:00+00:00"

SHEET = "docs/receiving.md"
INES_SHEET = """# Receiving a delivery

Check the paperwork against the load before anything comes off:

    count the pallets   compare with the delivery note
    check the seals     refuse anything broken
    chilled loads       probe one case, log the reading

Then book the stock in and shelve it:

    book in   scanner, BOOK-IN, scan each pallet
"""


def setup(repo, state):
    shared_desk(repo, ANCHOR, branches=ALL_BRANCHES + ACT5_BRANCHES + ACT6_BRANCHES)

    diverge_from_head_office(
        repo,
        ANCHOR,
        theirs=[("Add chilled loads to receiving", INES, WHEN_INES, {SHEET: INES_SHEET})],
        ours=[("Remove the receiving sheet", None, WHEN_MINE, {SHEET: None})],
    )
