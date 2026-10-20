"""Unfinished work in one bay, and an urgent typo wanting a bay of its own.

Unlike the earlier interruption, the fix must not go straight onto main -
so the student has to stash, move, branch, fix, and come back.
"""

from level_helpers import fresh_desk

ANCHOR = "tutorial/act2-desk"
WHEN_TYPO = "2025-03-19T08:20:00+00:00"
WHEN_PAGE = "2025-03-19T08:50:00+00:00"

PAGE = """# Stocktake, 31 March

Count every bin in aisles A to C. Two people to an aisle: one counts,
one writes the figure down.
"""

WIP = PAGE + """
Scanner counts: TODO, check whether the scanner rounds part rolls.
"""


def setup(repo, state):
    fresh_desk(repo, ANCHOR)

    # The typo is already committed on main, so any branch cut from main
    # carries it. This is the one commit main is expected to have.
    guide = repo.read("docs/receiving.md")
    repo.write_file(
        "docs/receiving.md",
        guide.replace("compare with the delivery note", "compare with the delivary note"),
    )
    repo.commit("Tidy the receiving wording", date=WHEN_TYPO)

    repo.switch("stocktake-prep", create=True)
    repo.write_file("docs/stocktake.md", PAGE)
    repo.commit("Start the stocktake plan", date=WHEN_PAGE)
    # Pending, not committed: the work that has to be put aside.
    repo.write_file("docs/stocktake.md", WIP)
