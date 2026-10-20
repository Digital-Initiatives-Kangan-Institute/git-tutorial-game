"""Two commits landed at Head Office, and one of them is in the file the
student committed this morning - which is the reason to look before
merging, rather than a rule that says to.
"""

from level_helpers import ALL_BRANCHES, INES, THEO, publish, shared_desk

ANCHOR = "tutorial/act4-desk"
ACT4_BRANCHES = ("count-b15", "returns-procedure", "shift-report", "stocktake-plan")
WHEN_THEO = "2025-03-27T10:10:00+00:00"
WHEN_INES = "2025-03-27T10:35:00+00:00"
WHEN_MINE = "2025-03-27T09:50:00+00:00"

B15_OPEN = "**B-15 Cartons, double wall**\n\nNot counted yet.\n"
B15_COUNTED = "**B-15 Cartons, double wall**\n\n12 bundles in stock.\n"

HEADING = "# Aisle B stock\n"
WITH_B13 = """# Aisle B stock

**B-13 Tape, brown**

18 rolls in stock.
"""

LAST_ENTRY = "- Dispatch note for 3 March started.\n"
WITH_NOTE = "- Dispatch note for 3 March started.\n- B-15 cartons counted.\n"


def setup(repo, state):
    shared_desk(repo, ANCHOR, branches=ALL_BRANCHES + ACT4_BRANCHES)

    publish(
        repo,
        ANCHOR,
        [
            (
                "Count the B-15 cartons",
                THEO,
                WHEN_THEO,
                {"stock/aisle-b.md": lambda t: t.replace(B15_OPEN, B15_COUNTED)},
            ),
            (
                "Note the carton count in the log",
                INES,
                WHEN_INES,
                {"dispatch/log.md": lambda t: t.replace(LAST_ENTRY, WITH_NOTE)},
            ),
        ],
    )

    # The student's own morning: B-13, at the other end of the same sheet.
    repo.write_file("stock/aisle-b.md", repo.read("stock/aisle-b.md").replace(HEADING, WITH_B13, 1))
    repo.commit("Count the B-13 tape", date=WHEN_MINE)
