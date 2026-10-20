"""Yesterday's branch, deleted this morning with -D.

Both commits are left unreachable but intact, which is the state a
student arrives in after agreeing with git's "not fully merged" warning
without reading it.
"""

from level_helpers import ALL_BRANCHES, fresh_desk

ANCHOR = "tutorial/act3-desk"
BRANCH = "fennick-note"
NOTE = "dispatch/2025-03-03.md"
WHEN_FIRST = "2025-03-24T15:40:00+00:00"
WHEN_SECOND = "2025-03-24T16:15:00+00:00"

UNFINISHED = "10:00. Each pallet is wrapped and labelled, and the third one is\n"
FINISHED = (
    "10:00. Each pallet is wrapped and labelled, and the third one is\n"
    "marked fragile because it carries the glass cloches.\n"
)
PALLETS = """
## Pallets

    1   compost, 40 bags
    2   terracotta pots, 60
    3   glass cloches, 24   FRAGILE
"""


def setup(repo, state):
    fresh_desk(repo, ANCHOR, branches=ALL_BRANCHES)

    repo.switch(BRANCH, create=True)
    repo.write_file(NOTE, repo.read(NOTE).replace(UNFINISHED, FINISHED))
    repo.commit("Finish the sentence about the third pallet", date=WHEN_FIRST)

    repo.write_file(NOTE, repo.read(NOTE) + PALLETS)
    repo.commit("List the pallets on the 3 March note", date=WHEN_SECOND)

    # Back to main, then delete the name. The commits stay on disk with
    # nothing pointing at them - which is the whole situation.
    repo.switch("main")
    repo.delete_branch(BRANCH, force=True)
