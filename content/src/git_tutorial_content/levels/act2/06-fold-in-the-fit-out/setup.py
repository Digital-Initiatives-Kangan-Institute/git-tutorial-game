"""A finished bay, and a main that has not moved since it opened.

Deliberately the easy shape: with nothing on main to reconcile, the merge
is a name moving forward, and the student sees that before they meet a
merge that has to combine anything.
"""

from level_helpers import fresh_desk

ANCHOR = "tutorial/act2-desk"
WHEN_ONE = "2025-03-13T09:20:00+00:00"
WHEN_TWO = "2025-03-13T11:45:00+00:00"

PAGE = """# Aisle D fit-out

New racking for aisle D goes in this week. Bays D-01 to D-12 will
hold the spring garden stock for Fennick Garden Centre.
"""

PAGE_DONE = PAGE + """
Each level of racking takes 500 kg. Heavy pallets go on the bottom
level only:

    D-01 to D-04   compost and bagged gravel
    D-05 to D-12   pots, trays and seed boxes
"""


def setup(repo, state):
    fresh_desk(repo, ANCHOR)

    repo.switch("aisle-d-fitout", create=True)
    repo.write_file("docs/aisle-d-fitout.md", PAGE)
    repo.commit("Describe the aisle D fit-out", date=WHEN_ONE)
    repo.write_file("docs/aisle-d-fitout.md", PAGE_DONE)
    repo.commit("List what goes in each aisle D bay", date=WHEN_TWO)
