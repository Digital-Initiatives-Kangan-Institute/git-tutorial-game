"""A dispatch note in the records stops mid-sentence. The student finishes it.

Nothing is fabricated: the unfinished note is already in the history.
Setup only returns the working tree to that state.
"""

ANCHOR = "tutorial/act1-desk"


def setup(repo, state):
    repo.require_refs(ANCHOR)
    repo.switch("main", create_if_missing_at=ANCHOR)
    repo.reset_hard(ANCHOR)
    repo.clean(untracked=True, ignored=True)
