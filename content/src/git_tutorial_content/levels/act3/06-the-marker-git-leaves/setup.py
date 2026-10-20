"""A morning's work, thrown away by one word.

Setup makes the three commits and then the bad reset, which leaves
ORIG_HEAD pointing at the tip that was lost - exactly as it would for a
student who typed --hard themselves. The three commits stay on disk,
unreachable.
"""

from level_helpers import ALL_BRANCHES, fresh_desk

ANCHOR = "tutorial/act3-desk"
WHEN_COUNT = "2025-03-27T09:05:00+00:00"
WHEN_LOG = "2025-03-27T09:40:00+00:00"
WHEN_RECEIPT = "2025-03-27T10:25:00+00:00"

NOT_COUNTED = "Not counted yet.\n"
COUNTED = "18 bundles on the shelf.\n"

COUNTED_ENTRY = "- Aisle B stock counted.\n"
WITH_B15 = "- Aisle B stock counted.\n- Bin B-15 counted.\n"

BOOK_IN = "    book in   scanner, BOOK-IN, scan each pallet\n"
WITH_RECEIPT = (
    "    book in   scanner, BOOK-IN, scan each pallet\n"
    "\nThe scanner prints a receipt: staple it to the delivery note.\n"
)


def setup(repo, state):
    fresh_desk(repo, ANCHOR, branches=ALL_BRANCHES)

    repo.write_file("stock/aisle-b.md", repo.read("stock/aisle-b.md").replace(NOT_COUNTED, COUNTED))
    repo.commit("Count bin B-15", date=WHEN_COUNT)

    repo.write_file("dispatch/log.md", repo.read("dispatch/log.md").replace(COUNTED_ENTRY, WITH_B15))
    repo.commit("Note the B-15 count in the log", date=WHEN_LOG)

    receiving = repo.read("docs/receiving.md")
    repo.write_file("docs/receiving.md", receiving.replace(BOOK_IN, WITH_RECEIPT))
    repo.commit("Say what to do with the scanner receipt", date=WHEN_RECEIPT)

    # The slip: --hard where --soft was meant. This is also what sets
    # ORIG_HEAD to the tip that is about to disappear.
    repo.git("reset", "--hard", "HEAD~3")
