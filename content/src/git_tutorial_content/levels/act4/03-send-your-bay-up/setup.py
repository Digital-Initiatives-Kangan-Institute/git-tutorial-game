"""Nothing to repair. The student has a count to book in on a branch of
its own, and the only new part is the last command.
"""

from level_helpers import ALL_BRANCHES, shared_desk

ANCHOR = "tutorial/act4-desk"
ACT4_BRANCHES = ("count-b15", "returns-procedure", "shift-report", "stocktake-plan")


def setup(repo, state):
    # shared_desk deletes every branch on Head Office except main, so a
    # count-b15 pushed by the last run is gone from there too.
    shared_desk(repo, ANCHOR, branches=ALL_BRANCHES + ACT4_BRANCHES)
