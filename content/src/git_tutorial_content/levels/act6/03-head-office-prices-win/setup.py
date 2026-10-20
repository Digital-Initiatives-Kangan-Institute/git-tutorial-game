"""Head Office's price list against the student's pencilled prices.

Ines sent the April price list up. The student, without pulling, had
already committed the prices Kestrelby's rep quoted on the phone, in the
same commit as a line in the dispatch log. The price list conflicts in
two blocks; the dispatch log merges cleanly.

Head Office is the authority on prices, so the answer is Ines's file
whole (`git restore --theirs`), and the student's log line still has to
survive: taking their side of one file is not throwing away the commit.
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
WHEN_INES = "2026-03-25T08:15:00+00:00"
WHEN_MINE = "2026-03-25T08:40:00+00:00"

APRIL_PRICES = """# Supplier prices

Prices agreed with Kestrelby Packaging, per unit, before VAT.

    [pallet-wrap]
    unit = "roll"
    price = 4.45

    [cartons]
    unit = "bundle of 25"
    price = 11.90

Prices hold until 30 June. After that, ask Head Office for the
new list before ordering.
"""

PRICE = "    price = 4.20\n"
HOLD = "Prices hold until 31 March."
MY_PRICE = "    price = 4.30\n"
MY_HOLD = "Prices hold until 30 April."

LAST_ENTRY = "- Dispatch note for 3 March started.\n"
MY_ENTRY = LAST_ENTRY + "- Kestrelby rang about pallet wrap prices.\n"


def setup(repo, state):
    shared_desk(repo, ANCHOR, branches=ALL_BRANCHES + ACT5_BRANCHES + ACT6_BRANCHES)

    diverge_from_head_office(
        repo,
        ANCHOR,
        theirs=[(
            "Send the April price list", INES, WHEN_INES,
            {"suppliers/price-list.md": APRIL_PRICES},
        )],
        ours=[(
            "Note the prices Kestrelby quoted", None, WHEN_MINE,
            {
                "suppliers/price-list.md":
                    lambda t: t.replace(PRICE, MY_PRICE).replace(HOLD, MY_HOLD),
                "dispatch/log.md": lambda t: t.replace(LAST_ENTRY, MY_ENTRY),
            },
        )],
    )
