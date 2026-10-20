"""Three pending changes with three different fates.

Earlier levels told the student what to do with a change. This one
gives them three and makes them decide, which is the actual skill.
"""

ANCHOR = "tutorial/act1-desk"

LOG_AFTER = "- Dispatch note for 3 March started.\n"
LOG_LINE = "- Opening checks written up.\n"
DRAFT = "\n**DRAFT - B-16 Strapping, 12mm**\n\nStill counting.\n"


def setup(repo, state):
    repo.require_refs(ANCHOR)
    repo.switch("main", create_if_missing_at=ANCHOR)
    repo.reset_hard(ANCHOR)
    repo.clean(untracked=True, ignored=True)

    # Finished, not staged: the thing that should be committed.
    log = repo.read("dispatch/log.md")
    repo.write_file("dispatch/log.md", log.replace(LOG_AFTER, LOG_AFTER + LOG_LINE))

    # Half-written, and staged: the thing that should come back out.
    aisle = repo.read("stock/aisle-b.md")
    repo.write_file("stock/aisle-b.md", aisle.rstrip("\n") + "\n" + DRAFT)
    repo.git("add", "stock/aisle-b.md")

    # A slip of the keyboard: the thing that should be thrown away.
    readme = repo.read("README.md")
    repo.write_file("README.md", readme.rstrip("\n") + "\nasdfasdf\n")
