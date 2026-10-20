"""The student arrives mid-conflict, which is how this usually happens.

Setup leaves MERGE_HEAD in place and the file marked up, so the level
starts in the state the last one taught them to escape from.
"""

from level_helpers import THEO, fresh_desk

ANCHOR = "tutorial/act2-desk"
WHEN_MAIN = "2025-03-18T09:30:00+00:00"
WHEN_BRANCH = "2025-03-18T10:05:00+00:00"

ORIGINAL = "40 rolls on the shelf.\n"
MAIN_SAYS = "38 rolls on the shelf after the Fennick order.\n"
BRANCH_SAYS = "36 rolls on the shelf. Two were torn and binned.\n"


def setup(repo, state):
    # First of all, because everything below needs a repository that is not
    # halfway through something - including a re-run of this very script.
    # fresh_desk aborts the merge, discards, cleans and only then switches.
    fresh_desk(repo, ANCHOR)

    repo.switch("recount-b14", create=True)
    stock = repo.read("stock/aisle-b.md")
    repo.write_file("stock/aisle-b.md", stock.replace(ORIGINAL, BRANCH_SAYS))
    repo.commit("Recount B-14", date=WHEN_BRANCH)

    repo.switch("main")
    stock = repo.read("stock/aisle-b.md")
    repo.write_file("stock/aisle-b.md", stock.replace(ORIGINAL, MAIN_SAYS))
    repo.commit("Take the Fennick order off B-14", date=WHEN_MAIN, author=THEO)

    # Leave it paused, mid-conflict. This is the level's starting state.
    repo.git("merge", "recount-b14", check=False)
