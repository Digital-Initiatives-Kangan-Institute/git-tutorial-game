"""Both lines have moved. This is the shape a fast-forward cannot fix.

The two sides touch different files, so git combines them without help -
the point of the level is the merge commit, not conflict resolution.
"""

from level_helpers import THEO, fresh_desk

ANCHOR = "tutorial/act2-desk"
WHEN_MAIN = "2025-03-14T08:40:00+00:00"
WHEN_BRANCH = "2025-03-14T10:15:00+00:00"

PAGE = """# Racking checks

Walk every aisle on Monday morning, before the first delivery.

    bent upright     tape the bay off and tell Marta
    missing pin      refit it before anything is loaded
"""

AFTER = "- Dispatch note for 3 March started.\n"
LINE = "- Fennick order dispatched.\n"


def setup(repo, state):
    fresh_desk(repo, ANCHOR)

    # Your bay, parted from the shared commit.
    repo.switch("racking-checks", create=True)
    repo.write_file("docs/racking-checks.md", PAGE)
    repo.commit("Add the weekly racking checks", date=WHEN_BRANCH)

    # Theo, meanwhile, on main. A different file, so the merge itself is
    # clean and the lesson stays on the shape.
    repo.switch("main")
    log = repo.read("dispatch/log.md")
    repo.write_file("dispatch/log.md", log.replace(AFTER, AFTER + LINE))
    repo.commit("Log the Fennick dispatch", date=WHEN_MAIN, author=THEO)

    repo.switch("racking-checks")
