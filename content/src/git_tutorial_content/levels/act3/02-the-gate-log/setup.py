"""Last night's accident, waiting on the desk this morning.

The reset is done by setup rather than asked of the student, because the
level is about reading the record of a mistake - and a student who has
just made the mistake themselves already knows the answer.
"""

from level_helpers import ALL_BRANCHES, fresh_desk

ANCHOR = "tutorial/act3-desk"


def setup(repo, state):
    fresh_desk(repo, ANCHOR, branches=ALL_BRANCHES)
    # One commit thrown away. `--hard` so the working tree matches, which
    # is what makes it look like the commit was never there.
    repo.git("reset", "--hard", "HEAD~1")
