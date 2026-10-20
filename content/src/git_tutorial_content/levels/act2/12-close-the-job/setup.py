"""Two files, both edited on both sides, in one merge.

Resolving one and committing is the mistake this level is shaped to
catch: git will refuse, and status keeps the score.
"""

from level_helpers import THEO, fresh_desk

ANCHOR = "tutorial/act2-desk"
WHEN_MAIN = "2025-03-20T09:10:00+00:00"
WHEN_BRANCH = "2025-03-20T09:55:00+00:00"

README_LINE = "Deliveries outside these hours wait in the yard."
README_MAIN = "Deliveries outside these hours wait by gate 2."
README_BRANCH = "Deliveries outside these hours go to aisle D."

AFTER = "- Dispatch note for 3 March started.\n"
LOG_MAIN = "- Fennick order dispatched.\n"
LOG_BRANCH = "- Aisle D fit-out signed off.\n"


def _edit(repo, readme, log_line):
    repo.write_file("README.md", repo.read("README.md").replace(README_LINE, readme))
    repo.write_file("dispatch/log.md", repo.read("dispatch/log.md").replace(AFTER, AFTER + log_line))


def setup(repo, state):
    fresh_desk(repo, ANCHOR)

    # The README already has a line both sides will rewrite, so the two
    # branches can part straight from the anchor.
    repo.switch("aisle-d-signoff", create=True)
    _edit(repo, README_BRANCH, LOG_BRANCH)
    repo.commit("Sign off the aisle D fit-out", date=WHEN_BRANCH)

    repo.switch("main")
    _edit(repo, README_MAIN, LOG_MAIN)
    repo.commit("Log the Fennick dispatch", date=WHEN_MAIN, author=THEO)
