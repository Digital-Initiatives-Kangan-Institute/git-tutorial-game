"""Last week's revert, which turned out to be the wrong call.

The revert commit is written by hand rather than by `git revert`, for
one reason: the real command stamps the commit with the clock, and a
level setup that mints a different sha on every run is not idempotent.
Nothing the student can see is different - a revert is an ordinary
commit with a conventional message.
"""

from level_helpers import ALL_BRANCHES, fresh_desk

ANCHOR = "tutorial/act3-desk"
PRICES = "suppliers/price-list.md"
WHEN_DISCOUNT = "2025-03-31T09:15:00+00:00"
WHEN_LOG = "2025-03-31T09:30:00+00:00"
WHEN_REVERT = "2025-04-01T16:50:00+00:00"

DISCOUNT = """
## Bulk discount

Kestrelby take 10% off any order over 50 rolls of pallet wrap.
"""

LAST_ENTRY = "- Dispatch note for 3 March started.\n"
WITH_DISCOUNT = "- Dispatch note for 3 March started.\n- Bulk discount recorded.\n"


def setup(repo, state):
    fresh_desk(repo, ANCHOR, branches=ALL_BRANCHES)

    discounted = repo.read(PRICES) + DISCOUNT
    repo.write_file(PRICES, discounted)
    repo.commit("Add the Kestrelby bulk discount", date=WHEN_DISCOUNT)

    repo.write_file("dispatch/log.md", repo.read("dispatch/log.md").replace(LAST_ENTRY, WITH_DISCOUNT))
    repo.commit("Note the bulk discount in the log", date=WHEN_LOG)

    # The revert: the discount taken out again, the log left alone.
    repo.write_file(PRICES, discounted.replace(DISCOUNT, ""))
    repo.commit('Revert "Add the Kestrelby bulk discount"', date=WHEN_REVERT)
