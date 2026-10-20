"""Two branches that have both moved since they parted.

Nothing to do but read: the point of the level is that the shape is
invisible until you ask for it, and obvious the moment you do.

The answer key depends on this shape - two commits on the bay, one on
main, parted at the act2-desk anchor - and tests/test_levels.py checks
it against the repository.
"""

from level_helpers import THEO, fresh_desk

ANCHOR = "tutorial/act2-desk"

WHEN_MAIN = "2025-03-11T10:00:00+00:00"
WHEN_ONE = "2025-03-11T11:30:00+00:00"
WHEN_TWO = "2025-03-11T14:05:00+00:00"

PAGE = """# Aisle D fit-out

New racking for aisle D goes in this week. Bays D-01 to D-12 will
hold the spring garden stock for Fennick Garden Centre.
"""

PAGE_MORE = PAGE + """
Each level of racking takes 500 kg. Heavy pallets go on the bottom
level only.
"""

AFTER = "- Dispatch note for 3 March started.\n"
LINE = "- Fennick order dispatched.\n"


def setup(repo, state):
    fresh_desk(repo, ANCHOR)

    # The bay first, so it parts from the shared commit rather than from
    # Theo's work.
    repo.switch("aisle-d-fitout", create=True)
    repo.write_file("docs/aisle-d-fitout.md", PAGE)
    repo.commit("Describe the aisle D fit-out", date=WHEN_ONE)
    repo.write_file("docs/aisle-d-fitout.md", PAGE_MORE)
    repo.commit("Add the racking load limit", date=WHEN_TWO)

    # Meanwhile Theo booked something in on main.
    repo.switch("main")
    log = repo.read("dispatch/log.md")
    repo.write_file("dispatch/log.md", log.replace(AFTER, AFTER + LINE))
    repo.commit("Log the Fennick dispatch", date=WHEN_MAIN, author=THEO)
