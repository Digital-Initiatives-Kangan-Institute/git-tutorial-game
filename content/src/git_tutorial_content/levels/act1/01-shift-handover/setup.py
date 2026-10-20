"""Level 1.1 only reads. Nothing to fabricate, only a clean checkout.

The canonical idempotent preamble: require, switch, reset, clean. The
order matters - cleaning after planting would delete the plant.
"""

ANCHOR = "tutorial/act1-desk"


def setup(repo, state):
    repo.require_refs(ANCHOR)
    repo.switch("main", create_if_missing_at=ANCHOR)
    repo.reset_hard(ANCHOR)
    repo.clean(untracked=True, ignored=True)
