"""The same line, counted two different ways.

Both sides edit bin B-14's count in stock/aisle-b.md, so git cannot pick
and has to hand the decision back.
"""

from level_helpers import THEO, fresh_desk

ANCHOR = "tutorial/act2-desk"
WHEN_MAIN = "2025-03-17T09:30:00+00:00"
WHEN_BRANCH = "2025-03-17T10:05:00+00:00"

ORIGINAL = "40 rolls on the shelf.\n"
MAIN_SAYS = "38 rolls on the shelf after the Fennick order.\n"
BRANCH_SAYS = "36 rolls on the shelf. Two were torn and binned.\n"


def setup(repo, state):
    # fresh_desk abandons a paused merge from a previous attempt first.
    fresh_desk(repo, ANCHOR)

    repo.switch("recount-b14", create=True)
    stock = repo.read("stock/aisle-b.md")
    repo.write_file("stock/aisle-b.md", stock.replace(ORIGINAL, BRANCH_SAYS))
    repo.commit("Recount B-14", date=WHEN_BRANCH)

    repo.switch("main")
    stock = repo.read("stock/aisle-b.md")
    repo.write_file("stock/aisle-b.md", stock.replace(ORIGINAL, MAIN_SAYS))
    repo.commit("Take the Fennick order off B-14", date=WHEN_MAIN, author=THEO)
