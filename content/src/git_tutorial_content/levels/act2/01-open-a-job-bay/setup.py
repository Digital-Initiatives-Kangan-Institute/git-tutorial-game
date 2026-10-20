"""A clean desk at the end of Act 1, and no bay opened yet.

The level is only about making one, so nothing is planted: the lesson is
that branching changes where commits will go and leaves the files alone.
"""

from level_helpers import fresh_desk

ANCHOR = "tutorial/act2-desk"


def setup(repo, state):
    # fresh_desk deletes every Act 2 branch, aisle-d-fitout included, so a
    # re-run undoes the level rather than preserving it.
    fresh_desk(repo, ANCHOR)
