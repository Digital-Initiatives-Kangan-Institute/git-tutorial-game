"""The student arrives already detached, because that is how it happens.

Nobody decides to detach HEAD. They paste a command from an answer that
told them to look at an old version, and the prompt changes.
"""

from level_helpers import ALL_BRANCHES, fresh_desk

ANCHOR = "tutorial/act3-desk"


def setup(repo, state):
    fresh_desk(repo, ANCHOR, branches=ALL_BRANCHES)
    # The commit the answer told them to look at: Theo's aisle B count.
    # Named by ref rather than counted back from the tip, so the answer key
    # cannot drift from the commit the student lands on.
    repo.require_refs("tutorial/c08")
    repo.git("checkout", "--detach", "refs/tutorial/c08")
