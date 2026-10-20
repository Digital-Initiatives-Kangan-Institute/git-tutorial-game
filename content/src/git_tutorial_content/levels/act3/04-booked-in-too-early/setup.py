"""The commit is already made, one line short of what it should say.

Setup commits so the student arrives having just done it - the moment
this level is about is the half-second after you press enter, not the
work that led up to it.
"""

from level_helpers import ALL_BRANCHES, fresh_desk

ANCHOR = "tutorial/act3-desk"
LOG = "dispatch/log.md"
WHEN = "2025-03-25T09:20:00+00:00"

LAST_ENTRY = "- Dispatch note for 3 March started.\n"
WITH_ONE_LINE = (
    "- Dispatch note for 3 March started.\n"
    "- Fennick Garden Centre order dispatched.\n"
)


def setup(repo, state):
    fresh_desk(repo, ANCHOR, branches=ALL_BRANCHES)

    repo.write_file(LOG, repo.read(LOG).replace(LAST_ENTRY, WITH_ONE_LINE, 1))
    repo.commit("Log the Fennick dispatch", date=WHEN)
