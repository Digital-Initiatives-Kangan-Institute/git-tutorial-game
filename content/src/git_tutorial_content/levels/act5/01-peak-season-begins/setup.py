"""Peak season opens with the act's habit: take Head Office's updates,
then branch, then send the branch up.

Theo really has sent a commit up overnight, so the student's `main` is one
behind Head Office. A branch made before pulling is built on last week's
records, and the second goal tells the two orders apart.
"""

from level_helpers import ACT5_BRANCHES, ALL_BRANCHES, THEO, publish, shared_desk

ANCHOR = "tutorial/act5-desk"
WHEN_THEO = "2025-04-07T06:10:00+00:00"

SATURDAY = "    Saturday           07:00 - 11:00\n"
WITH_SUNDAY = SATURDAY + "    Sunday (peak)      08:00 - 12:00\n"


def setup(repo, state):
    # Clears last run's peak-rota here and at Head Office.
    shared_desk(repo, ANCHOR, branches=ALL_BRANCHES + ACT5_BRANCHES)

    publish(
        repo,
        ANCHOR,
        [(
            "Open on Sundays for peak season",
            THEO,
            WHEN_THEO,
            {"README.md": lambda t: t.replace(SATURDAY, WITH_SUNDAY)},
        )],
    )
