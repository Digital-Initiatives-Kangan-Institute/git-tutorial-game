"""Nothing fabricated. The repository the student has worked in since
the first shift has been a clone all along, and the act opens by saying so.
"""

from level_helpers import ALL_BRANCHES, shared_desk

ANCHOR = "tutorial/act4-desk"

# Branches act 4 opens. They are not in level_helpers' lists, so every act 4
# setup clears them itself: a student playing straight through would
# otherwise find the last job's branch still standing in this one.
ACT4_BRANCHES = ("count-b15", "returns-procedure", "shift-report", "stocktake-plan")


def setup(repo, state):
    shared_desk(repo, ANCHOR, branches=ALL_BRANCHES + ACT4_BRANCHES)
