"""A mess, none of it committed.

One change is staged and one is not, because the whole lesson is that
those are different places needing different commands.
"""

ANCHOR = "tutorial/act1-desk"

BLOCK = '    [pallet-wrap]\n    unit = "roll"\n    price = 4.20\n'
JUNK = "\nTODO recount all of this\n"


def setup(repo, state):
    repo.require_refs(ANCHOR)
    repo.switch("main", create_if_missing_at=ANCHOR)
    repo.reset_hard(ANCHOR)
    repo.clean(untracked=True, ignored=True)

    # Staged: the price list with its pallet-wrap block pasted twice.
    prices = repo.read("suppliers/price-list.md")
    repo.write_file("suppliers/price-list.md", prices.replace(BLOCK, BLOCK + "\n" + BLOCK))
    repo.git("add", "suppliers/price-list.md")

    # Not staged: a scribble on the aisle B sheet that should never be booked.
    aisle = repo.read("stock/aisle-b.md")
    repo.write_file("stock/aisle-b.md", aisle.rstrip("\n") + "\n" + JUNK)
