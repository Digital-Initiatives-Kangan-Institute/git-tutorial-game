"""A bay with one commit on it, and HEAD left standing in that bay.

The level is the moment a beginner is most sure they have lost their
work: the file disappears from the folder when they switch away.
"""

from level_helpers import fresh_desk

ANCHOR = "tutorial/act2-desk"

# Pinned so re-running setup rebuilds the identical commit. Without it the
# real clock mints a new sha every time and a reset would not be a reset.
WHEN = "2025-03-10T09:15:00+00:00"

PAGE = """# Aisle D fit-out

New racking for aisle D goes in this week. Bays D-01 to D-12 will
hold the spring garden stock for Fennick Garden Centre.
"""


def setup(repo, state):
    fresh_desk(repo, ANCHOR)

    repo.switch("aisle-d-fitout", create=True)
    repo.write_file("docs/aisle-d-fitout.md", PAGE)
    repo.commit("Describe the aisle D fit-out", date=WHEN)
