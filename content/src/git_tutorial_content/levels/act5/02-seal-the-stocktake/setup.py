"""Marta signed off Theo's aisle B count (c08) as the March stocktake
figure. Two commits have landed on top of it since, so `git tag` with no
commit named would seal the wrong one.

`shared_desk` removes every tag here and at Head Office, so
`stocktake-march` genuinely exists nowhere until the student makes it.
"""

from level_helpers import ACT5_BRANCHES, ALL_BRANCHES, shared_desk

ANCHOR = "tutorial/act5-desk"


def setup(repo, state):
    shared_desk(repo, ANCHOR, branches=ALL_BRANCHES + ACT5_BRANCHES)
