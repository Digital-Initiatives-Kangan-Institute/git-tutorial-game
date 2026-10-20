"""The student committed before lunch. Ines sent a commit up during it.

Theirs is local and hers is at Head Office, so the first thing the
student does this afternoon is the push that gets rejected.
"""

from level_helpers import ALL_BRANCHES, INES, publish, shared_desk

ANCHOR = "tutorial/act4-desk"
ACT4_BRANCHES = ("count-b15", "returns-procedure", "shift-report", "stocktake-plan")
WHEN_INES = "2025-03-26T12:20:00+00:00"
WHEN_MINE = "2025-03-26T11:45:00+00:00"

OLD_PRICE = "    unit = \"roll\"\n    price = 4.20\n"
NEW_PRICE = "    unit = \"roll\"\n    price = 4.35\n"

AFTER_HOURS = """
## After hours

Deliveries after 14:00 are signed for by the shift lead, not the
driver's mate.
"""


def setup(repo, state):
    shared_desk(repo, ANCHOR, branches=ALL_BRANCHES + ACT4_BRANCHES)

    publish(
        repo,
        ANCHOR,
        [(
            "Correct the pallet wrap price",
            INES,
            WHEN_INES,
            {"suppliers/price-list.md": lambda t: t.replace(OLD_PRICE, NEW_PRICE)},
        )],
    )

    repo.write_file("docs/receiving.md", repo.read("docs/receiving.md") + AFTER_HOURS)
    repo.commit("Write up after-hours deliveries", date=WHEN_MINE)
