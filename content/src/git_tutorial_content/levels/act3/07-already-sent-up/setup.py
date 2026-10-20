"""A wrong commit with two good ones sitting on top of it.

The two above are what make `reset` the wrong answer: moving the label
back far enough to lose the mistake would lose them as well. That is
the everyday version of "Head Office already has it", and it needs no
remote to be true.
"""

from level_helpers import ALL_BRANCHES, fresh_desk

ANCHOR = "tutorial/act3-desk"
WHEN_PRICE = "2025-03-28T10:00:00+00:00"
WHEN_COUNT = "2025-03-28T11:30:00+00:00"
WHEN_LOG = "2025-03-28T11:45:00+00:00"

# The price Ines read off the wrong line of Kestrelby's quote.
RIGHT_PRICE = '    unit = "roll"\n    price = 4.20\n'
WRONG_PRICE = '    unit = "roll"\n    price = 2.40\n'

NOT_COUNTED = "Not counted yet.\n"
COUNTED = "18 bundles on the shelf.\n"

COUNTED_ENTRY = "- Aisle B stock counted.\n"
WITH_B15 = "- Aisle B stock counted.\n- Bin B-15 counted.\n"


def setup(repo, state):
    fresh_desk(repo, ANCHOR, branches=ALL_BRANCHES)

    prices = repo.read("suppliers/price-list.md")
    repo.write_file("suppliers/price-list.md", prices.replace(RIGHT_PRICE, WRONG_PRICE))
    repo.commit("Update the pallet wrap price", date=WHEN_PRICE)

    repo.write_file("stock/aisle-b.md", repo.read("stock/aisle-b.md").replace(NOT_COUNTED, COUNTED))
    repo.commit("Count bin B-15", date=WHEN_COUNT)

    repo.write_file("dispatch/log.md", repo.read("dispatch/log.md").replace(COUNTED_ENTRY, WITH_B15))
    repo.commit("Note the B-15 count in the log", date=WHEN_LOG)
