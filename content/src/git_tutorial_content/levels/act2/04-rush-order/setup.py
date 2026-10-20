"""Half-finished work in a bay, and an urgent one-liner wanted on main.

The stocktake page is committed on the branch but the latest edit is not,
and the file does not exist on main at all - so git will refuse to switch
and the student has to deal with the pending work rather than route
around it.
"""

from level_helpers import fresh_desk

ANCHOR = "tutorial/act2-desk"
WHEN = "2025-03-12T09:00:00+00:00"

PAGE = """# Stocktake, 31 March

Count every bin in aisles A to C. Two people to an aisle: one counts,
one writes the figure down.
"""

WIP = PAGE + """
Scanner counts: TODO, check whether the scanner rounds part rolls.
"""


def setup(repo, state):
    # fresh_desk drops pending changes and the stash before it switches, so
    # a re-run is not refused the switch by its own leftovers.
    fresh_desk(repo, ANCHOR)

    repo.switch("stocktake-prep", create=True)
    repo.write_file("docs/stocktake.md", PAGE)
    repo.commit("Start the stocktake plan", date=WHEN)

    # Pending, not committed: this is the work that has to go somewhere.
    repo.write_file("docs/stocktake.md", WIP)
