"""A conflicted merge of the wrong branch, already in progress.

Both branches are left standing: the fix the student wanted, and the
month-end close that is not ready. The conflict is incidental - it is
simply what made them look.
"""

from level_helpers import ALL_BRANCHES, fresh_desk

ANCHOR = "tutorial/act3-desk"
WHEN_HOTFIX = "2025-04-02T09:10:00+00:00"
WHEN_MONTH_END = "2025-04-02T09:35:00+00:00"
WHEN_MAIN = "2025-04-02T10:15:00+00:00"

CARTONS = '    unit = "bundle of 25"\n    price = 11.50\n'
CARTONS_FIXED = (
    '    unit = "bundle of 25"\n    price = 11.50\n\n'
    "Cartons are sold by the bundle. Never split a bundle.\n"
)

THIS_WEEK = "## This week\n"
WEEK_ENDING = "## Week ending 28 March\n"

# Both branches rewrite this line. The conflict has to be real: an edit
# month-end makes elsewhere in the file would merge cleanly and the
# student would never be stopped to look at what they typed.
PLANNED = "Stocktake is planned for the end of the month.\n"
DONE = "Stocktake completed on 31 March.\n"
SLIPPED = "Stocktake is planned for the first week of April.\n"


def setup(repo, state):
    fresh_desk(repo, ANCHOR, branches=ALL_BRANCHES)

    repo.switch("hotfix", create=True)
    prices = repo.read("suppliers/price-list.md")
    repo.write_file("suppliers/price-list.md", prices.replace(CARTONS, CARTONS_FIXED))
    repo.commit("Say that cartons are never split", date=WHEN_HOTFIX)

    repo.switch("main")
    repo.switch("month-end", create=True)
    log = repo.read("dispatch/log.md").replace(THIS_WEEK, WEEK_ENDING)
    repo.write_file("dispatch/log.md", log.replace(PLANNED, DONE))
    repo.commit("Close the month", date=WHEN_MONTH_END)

    repo.switch("main")
    repo.write_file("dispatch/log.md", repo.read("dispatch/log.md").replace(PLANNED, SLIPPED))
    repo.commit("Say the stocktake has slipped a week", date=WHEN_MAIN)

    # The wrong branch, merged. It conflicts, which is the only reason
    # anybody looks at what they typed.
    repo.git("merge", "month-end", check=False)
