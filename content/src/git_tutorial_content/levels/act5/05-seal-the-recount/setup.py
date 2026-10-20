"""Theo recounted B-14 before the Easter rush and typed the new figure into
the aisle B sheet on the shared terminal, then went out to the dock.

The change is really there, uncommitted, in the student's working tree.
Nothing is committed, pushed or tagged: all three are the student's job,
and the tag must end up on the commit that holds the recount, at Head
Office as well as here.
"""

from level_helpers import ACT5_BRANCHES, ALL_BRANCHES, shared_desk

ANCHOR = "tutorial/act5-desk"

COUNTED = "40 rolls on the shelf.\n"
RECOUNTED = "36 rolls on the shelf. Recounted 9 April.\n"


def setup(repo, state):
    shared_desk(repo, ANCHOR, branches=ALL_BRANCHES + ACT5_BRANCHES)
    repo.write_file(
        "stock/aisle-b.md", repo.read("stock/aisle-b.md").replace(COUNTED, RECOUNTED)
    )
