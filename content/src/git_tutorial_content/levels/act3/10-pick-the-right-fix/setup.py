"""Three messes at three different stages, which is what a real morning
looks like. Nothing here is harder than the levels before it; the level
is about telling them apart.
"""

from level_helpers import ALL_BRANCHES, fresh_desk

ANCHOR = "tutorial/act3-desk"
WHEN_PRICE = "2025-04-03T09:05:00+00:00"
WHEN_LOG = "2025-04-03T09:20:00+00:00"
WHEN_WIP = "2025-04-04T17:55:00+00:00"

RIGHT_PRICE = '    unit = "roll"\n    price = 4.20\n'
WRONG_PRICE = '    unit = "roll"\n    price = 2.40\n'

LAST_ENTRY = "- Dispatch note for 3 March started.\n"
WITH_NOTE = "- Dispatch note for 3 March started.\n- Pallet wrap price updated.\n"

# Last night's stopping point: a section begun and thought better of.
WIP_SECTION = """
## Returns

Returned stock goes to
"""

# Never committed: this morning, interrupted mid-sentence.
HALF_TYPED = "\n**B-16 Tape, brown**\n\nAbout 30 rolls, if you count the\n"


def setup(repo, state):
    fresh_desk(repo, ANCHOR, branches=ALL_BRANCHES)

    # Shared: two commits Head Office already has.
    prices = repo.read("suppliers/price-list.md")
    repo.write_file("suppliers/price-list.md", prices.replace(RIGHT_PRICE, WRONG_PRICE))
    repo.commit("Update the pallet wrap price", date=WHEN_PRICE)

    repo.write_file("dispatch/log.md", repo.read("dispatch/log.md").replace(LAST_ENTRY, WITH_NOTE))
    repo.commit("Note the new price in the log", date=WHEN_LOG)

    # Yours alone: last night's commit, made to stop for the day.
    repo.write_file("docs/receiving.md", repo.read("docs/receiving.md") + WIP_SECTION)
    repo.commit("WIP: start on the returns section", date=WHEN_WIP)

    repo.write_file("stock/aisle-b.md", repo.read("stock/aisle-b.md") + HALF_TYPED)
