"""Two pending changes in different states, and a reason to leave them.

One staged, one not. Stash takes both, which is the thing people do not
believe until they watch it happen.
"""

from level_helpers import fresh_desk

ANCHOR = "tutorial/act2-desk"
WHEN = "2025-03-15T09:00:00+00:00"

AFTER = "- Dispatch note for 3 March started.\n"
LINE = "- Cartons in B-15 counted.\n"


def setup(repo, state):
    fresh_desk(repo, ANCHOR)

    repo.switch("aisle-b-count", create=True)
    # An empty commit so the branch is its own thing before the edits land.
    repo.commit("Start the aisle B count", allow_empty=True, date=WHEN)

    # Staged: the count itself.
    stock = repo.read("stock/aisle-b.md")
    repo.write_file(
        "stock/aisle-b.md",
        stock.replace("Not counted yet.", "22 bundles on the shelf."),
    )
    repo.git("add", "stock/aisle-b.md")

    # Not staged: the log line that goes with it.
    log = repo.read("dispatch/log.md")
    repo.write_file("dispatch/log.md", log.replace(AFTER, AFTER + LINE))
