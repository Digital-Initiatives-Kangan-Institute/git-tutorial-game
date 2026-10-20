"""One commit holding a real edit and a private file.

The pairing is the point: `git add .` does not distinguish between the
thing you were working on and the thing that happened to be in the
folder, and neither does the commit that follows it.
"""

from level_helpers import ALL_BRANCHES, fresh_desk

ANCHOR = "tutorial/act3-desk"
WHEN = "2025-03-26T11:05:00+00:00"

PROCEDURES = "- [Supplier prices](suppliers/price-list.md)\n"
WITH_LOG = (
    "- [Supplier prices](suppliers/price-list.md)\n"
    "- [Dispatch log](dispatch/log.md)\n"
)
NOTES = """# Notes

- ask Ines when the new price list lands
- the 3 March note still reads like a draft
- do not let this file anywhere near the records
"""


def setup(repo, state):
    fresh_desk(repo, ANCHOR, branches=ALL_BRANCHES)

    repo.write_file("README.md", repo.read("README.md").replace(PROCEDURES, WITH_LOG))
    repo.write_file("scratch.md", NOTES)
    # `git add .` is the habit this level is about, so setup uses it too.
    repo.git("add", ".")
    repo.commit("Link the dispatch log", add_all=False, date=WHEN)
