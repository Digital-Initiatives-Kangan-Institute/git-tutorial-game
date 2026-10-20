"""A clean desk and a job. Nothing is planted: the work is the point."""

from level_helpers import fresh_desk

ANCHOR = "tutorial/act2-desk"


def setup(repo, state):
    fresh_desk(repo, ANCHOR)
