"""Ines sent a commit up while the student was writing their log line.

Hers goes to Head Office and is wound back out of the clone, so the
student's repository is what it would really be: one commit of their own,
and no idea yet that Head Office has moved.
"""

from level_helpers import ALL_BRANCHES, INES, publish, shared_desk

ANCHOR = "tutorial/act4-desk"
ACT4_BRANCHES = ("count-b15", "returns-procedure", "shift-report", "stocktake-plan")
WHEN_INES = "2025-03-25T09:40:00+00:00"
WHEN_MINE = "2025-03-25T10:05:00+00:00"

DAMAGED = """
## Damaged stock

If a pallet arrives damaged, photograph it before signing for it.
"""

LAST_ENTRY = "- Dispatch note for 3 March started.\n"
WITH_NOTE = "- Dispatch note for 3 March started.\n- Damaged stock procedure added.\n"


def setup(repo, state):
    shared_desk(repo, ANCHOR, branches=ALL_BRANCHES + ACT4_BRANCHES)

    publish(
        repo,
        ANCHOR,
        [(
            "Add a damaged stock section",
            INES,
            WHEN_INES,
            {"docs/receiving.md": lambda text: text + DAMAGED},
        )],
    )

    # The student's own morning, committed locally and not yet sent up.
    repo.write_file("dispatch/log.md", repo.read("dispatch/log.md").replace(LAST_ENTRY, WITH_NOTE))
    repo.commit("Note the damaged stock procedure", date=WHEN_MINE)
