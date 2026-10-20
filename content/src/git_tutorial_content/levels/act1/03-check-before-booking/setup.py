"""Two changed files, only one of them staged.

The point of the level is that `git diff` and `git diff --staged` show
disjoint sets, so the plant must leave one change in each.
"""

ANCHOR = "tutorial/act1-desk"

LOG_AFTER = "- Dispatch note for 3 March started.\n"
LOG_LINE = "- Safety sheet booked in.\n"
AISLE_LINES = "\n**B-16 Strapping, 12mm**\n\nNot counted yet.\n"


def setup(repo, state):
    repo.require_refs(ANCHOR)
    repo.switch("main", create_if_missing_at=ANCHOR)
    repo.reset_hard(ANCHOR)
    repo.clean(untracked=True, ignored=True)

    log = repo.read("dispatch/log.md")
    repo.write_file("dispatch/log.md", log.replace(LOG_AFTER, LOG_AFTER + LOG_LINE))
    repo.git("add", "dispatch/log.md")

    aisle = repo.read("stock/aisle-b.md")
    repo.write_file("stock/aisle-b.md", aisle.rstrip("\n") + "\n" + AISLE_LINES)
