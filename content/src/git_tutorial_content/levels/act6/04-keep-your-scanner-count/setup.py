"""The scanner against the clipboard.

Theo typed up last week's paper count of aisle B and sent it to Head
Office, with a line in the dispatch log. The student scanned aisle B
this morning and committed the fresh figures without pulling. The stock
sheet conflicts; the dispatch log merges cleanly.

The scan is the newer count, so the answer is the student's sheet whole
(`git restore --ours`), while Theo's log line still comes in.
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
WHEN_THEO = "2026-03-25T13:20:00+00:00"
WHEN_MINE = "2026-03-25T14:05:00+00:00"

B14 = "40 rolls on the shelf.\n"
B15 = "Not counted yet.\n"

LAST_ENTRY = "- Dispatch note for 3 March started.\n"
THEO_ENTRY = LAST_ENTRY + "- Aisle B paper count typed up.\n"


def setup(repo, state):
    shared_desk(repo, ANCHOR, branches=ALL_BRANCHES + ACT5_BRANCHES + ACT6_BRANCHES)

    diverge_from_head_office(
        repo,
        ANCHOR,
        theirs=[(
            "Type up the aisle B paper count", THEO, WHEN_THEO,
            {
                "stock/aisle-b.md": lambda t: t.replace(B14, "36 rolls, paper count.\n")
                                               .replace(B15, "20 bundles, paper count.\n"),
                "dispatch/log.md": lambda t: t.replace(LAST_ENTRY, THEO_ENTRY),
            },
        )],
        ours=[(
            "Record the aisle B scan", None, WHEN_MINE,
            {"stock/aisle-b.md": lambda t: t.replace(B14, "41 rolls, scanned 25 March.\n")
                                            .replace(B15, "23 bundles, scanned 25 March.\n")},
        )],
    )
