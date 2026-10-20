"""Three things at once, each one real.

1. Yesterday the student fetched while Ines's `april-slots` draft was at
   Head Office. She has since withdrawn it, so `origin/april-slots` is a
   stale name.
2. Theo sent a commit up to main this morning, so Head Office's main has
   moved and the student's `origin/main` does not know.
3. The student committed their own work on main. Their push will be
   refused.

`git pull` does not prune, so the stale name survives the pull-and-push
fix and needs its own `git fetch --prune`.
"""

from level_helpers import (
    ACT5_BRANCHES,
    ALL_BRANCHES,
    INES,
    THEO,
    delete_at_head_office,
    publish,
    shared_desk,
)

ANCHOR = "tutorial/act5-desk"
WHEN_SLOTS = "2025-04-16T16:40:00+00:00"
WHEN_THEO = "2025-04-17T06:55:00+00:00"
WHEN_MINE = "2025-04-17T07:20:00+00:00"

SLOTS = "# April delivery slots (draft)\n\nTuesday and Thursday, 07:00.\n"

LAST_ENTRY = "- Dispatch note for 3 March started.\n"
WITH_EASTER = LAST_ENTRY + "- Easter dispatches booked for 17 and 18 April.\n"

LOADING_BAYS = """
## Peak season loading bays

During peak season, bays 3 and 4 are for outbound Easter orders only.
Inbound deliveries use bays 1 and 2.
"""


def setup(repo, state):
    # The fetch --prune inside shared_desk clears last run's stale name.
    shared_desk(repo, ANCHOR, branches=ALL_BRANCHES + ACT5_BRANCHES)

    # Yesterday afternoon: Ines's draft, fetched by the student.
    publish(
        repo, ANCHOR,
        [("Draft the April delivery slots", INES, WHEN_SLOTS, {"dispatch/slots.md": SLOTS})],
        branch="april-slots",
    )
    repo.git("fetch", "origin")
    delete_at_head_office(repo, "april-slots")

    # Early this morning: Theo, straight to main at Head Office.
    publish(
        repo, ANCHOR,
        [(
            "Log the Easter dispatches",
            THEO,
            WHEN_THEO,
            {"dispatch/log.md": lambda t: t.replace(LAST_ENTRY, WITH_EASTER)},
        )],
    )

    # And the student's own commit, made without pulling first.
    repo.write_file("docs/receiving.md", repo.read("docs/receiving.md") + LOADING_BAYS)
    repo.commit("Add the peak season loading bays", date=WHEN_MINE)
