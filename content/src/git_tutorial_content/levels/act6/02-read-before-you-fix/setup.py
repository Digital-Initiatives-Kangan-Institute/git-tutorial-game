"""One pull, two files, three conflict blocks.

At Head Office: Theo's B-14 count and Ines's new prices, two commits.
Here: the student's own B-14 count and the prices Kestrelby quoted on
the phone, two commits. Every one of them touches a line the other side
touched too, so the student's `git pull` stops with stock/aisle-b.md
(one block) and suppliers/price-list.md (two blocks) both conflicted.

Marta's rule settles it: counts are whoever counted on the floor (the
student), prices are Head Office's.
"""

from level_helpers import (
    ACT5_BRANCHES,
    ACT6_BRANCHES,
    ALL_BRANCHES,
    INES,
    THEO,
    diverge_from_head_office,
    shared_desk,
)

ANCHOR = "tutorial/act6-desk"
WHEN_THEO = "2026-03-24T07:50:00+00:00"
WHEN_INES = "2026-03-24T08:30:00+00:00"
WHEN_COUNT = "2026-03-24T08:05:00+00:00"
WHEN_PRICES = "2026-03-24T08:45:00+00:00"

COUNT = "40 rolls on the shelf.\n"
THEO_COUNT = "37 rolls counted for the stocktake.\n"
MY_COUNT = "39 rolls counted for the stocktake.\n"

PRICE = "    price = 4.20\n"
HOLD = "Prices hold until 31 March."
INES_PRICE = "    price = 4.45\n"
INES_HOLD = "Prices hold until 30 June."
MY_PRICE = "    price = 4.30\n"
MY_HOLD = "Prices hold until 30 April."


def setup(repo, state):
    shared_desk(repo, ANCHOR, branches=ALL_BRANCHES + ACT5_BRANCHES + ACT6_BRANCHES)

    diverge_from_head_office(
        repo,
        ANCHOR,
        theirs=[
            ("Count B-14 for the stocktake", THEO, WHEN_THEO,
             {"stock/aisle-b.md": lambda t: t.replace(COUNT, THEO_COUNT)}),
            ("Send the April price list", INES, WHEN_INES,
             {"suppliers/price-list.md":
              lambda t: t.replace(PRICE, INES_PRICE).replace(HOLD, INES_HOLD)}),
        ],
        ours=[
            ("Record my B-14 count", None, WHEN_COUNT,
             {"stock/aisle-b.md": lambda t: t.replace(COUNT, MY_COUNT)}),
            ("Note the prices Kestrelby quoted", None, WHEN_PRICES,
             {"suppliers/price-list.md":
              lambda t: t.replace(PRICE, MY_PRICE).replace(HOLD, MY_HOLD)}),
        ],
    )
