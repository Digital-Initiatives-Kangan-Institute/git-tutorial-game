"""The finale: one pull, three kinds of conflict.

Shared history first: Marta's stocktake checklist, already at Head
Office. Then, at Head Office: Theo's aisle B count, Ines's April price
list, and Ines retiring the checklist. Here, unpulled: the student's
aisle B scan, the prices Kestrelby quoted, and a tick on the checklist.

The pull stops on three files, each a different decision:
  stock/aisle-b.md            both changed  -> hand-merge (Theo's B-14, your B-15)
  suppliers/price-list.md     both changed  -> Head Office's whole (restore --theirs)
  docs/stocktake-checklist.md modify/delete -> retired (git rm)
Then the sign-off: tag `stocktake-final` on the merged, pushed commit.
"""

from level_helpers import (
    ACT5_BRANCHES,
    ACT6_BRANCHES,
    ALL_BRANCHES,
    INES,
    MARTA,
    THEO,
    diverge_from_head_office,
    shared_desk,
)

ANCHOR = "tutorial/act6-desk"
WHEN_CHECKLIST = "2026-03-20T09:00:00+00:00"
WHEN_THEO = "2026-03-27T09:30:00+00:00"
WHEN_PRICES = "2026-03-27T10:00:00+00:00"
WHEN_RETIRE = "2026-03-27T10:20:00+00:00"
WHEN_SCAN = "2026-03-27T09:45:00+00:00"
WHEN_TICK = "2026-03-27T10:30:00+00:00"

CHECKLIST = "docs/stocktake-checklist.md"
CHECKLIST_SHEET = """# Stocktake checklist

- [ ] Aisle B counted
- [ ] Prices checked against Head Office's list
- [ ] Counts signed off by Marta
"""

B14 = "40 rolls on the shelf.\n"
B15 = "Not counted yet.\n"

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


def setup(repo, state):
    # Clears last run's stocktake-final tag here and at Head Office too.
    shared_desk(repo, ANCHOR, branches=ALL_BRANCHES + ACT5_BRANCHES + ACT6_BRANCHES)

    # Shared history: the checklist both sides start from.
    repo.write_file(CHECKLIST, CHECKLIST_SHEET)
    base = repo.commit("Write the stocktake checklist", date=WHEN_CHECKLIST, author=MARTA)
    repo.git("push", "--force", "origin", "HEAD:refs/heads/main")

    diverge_from_head_office(
        repo,
        base,
        theirs=[
            ("Count aisle B for the final stocktake", THEO, WHEN_THEO,
             {"stock/aisle-b.md": lambda t: t.replace(B14, "38 rolls counted.\n")
                                             .replace(B15, "Count after the Fennick order.\n")}),
            ("Send the April price list", INES, WHEN_PRICES,
             {"suppliers/price-list.md": APRIL_PRICES}),
            ("Retire the stocktake checklist", INES, WHEN_RETIRE,
             {CHECKLIST: None}),
        ],
        ours=[
            ("Scan aisle B for the final stocktake", None, WHEN_SCAN,
             {"stock/aisle-b.md": lambda t: t.replace(B14, "39 rolls counted.\n")
                                             .replace(B15, "26 bundles counted.\n"),
              "suppliers/price-list.md":
                  lambda t: t.replace(PRICE, "    price = 4.30\n")
                             .replace(HOLD, "Prices hold until 30 April.")}),
            ("Tick off the stocktake checklist", None, WHEN_TICK,
             {CHECKLIST: lambda t: t.replace("- [ ] Aisle B", "- [x] Aisle B")
                                    .replace("- [ ] Prices", "- [x] Prices")}),
        ],
    )
