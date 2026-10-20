"""Plant an untracked file for the student's first commit.

Untracked rather than modified on purpose: the honest version of "your
first commit" is a file git has never heard of.
"""

ANCHOR = "tutorial/act1-desk"

SHEET = """\
# Safety on the floor

**Hi-vis on at all times** past the yellow line, including visitors.

**Pallet trucks are walked, not ridden.**

Report every spill to the shift lead before anyone cleans it up.
"""


def setup(repo, state):
    repo.require_refs(ANCHOR)
    repo.switch("main", create_if_missing_at=ANCHOR)
    repo.reset_hard(ANCHOR)
    repo.clean(untracked=True, ignored=True)
    repo.write_file("docs/safety.md", SHEET)
