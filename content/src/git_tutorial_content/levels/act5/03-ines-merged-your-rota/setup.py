"""Ines merged the student's `peak-rota` into main at Head Office.

The student is still on `peak-rota`, with its upstream set from last
job's `push -u`. Head Office really has the merge commit on main, and
still has the `peak-rota` branch; the student's `main` and `origin/main`
know nothing about the merge until they pull.

That gap is the point of `git branch -d`: it refuses while the branch is
unmerged as far as this repository knows, and agrees once `main` has been
pulled.
"""

from level_helpers import (
    ACT5_BRANCHES,
    ALL_BRANCHES,
    INES,
    merge_at_head_office,
    shared_desk,
)

ANCHOR = "tutorial/act5-desk"
WHEN_ROTA = "2025-04-07T09:20:00+00:00"
WHEN_MERGE = "2025-04-08T10:05:00+00:00"

ROTA = """# Peak season rota

    Mon - Fri   early 06:00 - 14:00   late 12:00 - 20:00
    Saturday    07:00 - 11:00

Theo leads the early shift. The trainee shadows the late shift in week one.
"""


def setup(repo, state):
    # Clears last run's peak-rota here and at Head Office.
    shared_desk(repo, ANCHOR, branches=ALL_BRANCHES + ACT5_BRANCHES)

    # Yesterday: the rota, sent up with `push -u`.
    repo.switch("peak-rota", create=True)
    repo.write_file("rota/peak.md", ROTA)
    repo.commit("Add the peak season rota", date=WHEN_ROTA)
    repo.git("push", "--force", "-u", "origin", "peak-rota")

    # This morning, at Head Office: Ines folds it into main.
    merge_at_head_office(
        repo, ANCHOR, "peak-rota",
        message="Merge the peak season rota", author=INES, date=WHEN_MERGE,
    )

    repo.switch("peak-rota")
