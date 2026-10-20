"""Ines sent a commit up to Head Office while the student was reading the
last job.

It is on the remote and the clone knows nothing about it, which is the
state every working day starts in.
"""

from level_helpers import ALL_BRANCHES, INES, publish, shared_desk

ANCHOR = "tutorial/act4-desk"
ACT4_BRANCHES = ("count-b15", "returns-procedure", "shift-report", "stocktake-plan")
WHEN = "2025-03-24T08:50:00+00:00"

UNTIL = "Prices hold until 31 March. After that, ask Head Office for the\n"
EXTENDED = (
    "Prices hold until 30 April. Kestrelby agreed the extra month on\n"
    "24 March. After that, ask Head Office for the\n"
)


def setup(repo, state):
    shared_desk(repo, ANCHOR, branches=ALL_BRANCHES + ACT4_BRANCHES)
    publish(
        repo,
        ANCHOR,
        [(
            "Extend the Kestrelby prices to 30 April",
            INES,
            WHEN,
            {"suppliers/price-list.md": lambda text: text.replace(UNTIL, EXTENDED)},
        )],
    )
