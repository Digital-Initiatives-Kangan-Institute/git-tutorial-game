"""The act's close: one branch taken all the way from finished to sealed
and cleared.

The student wrote the peak close-down on `peak-close` and pushed it with
`push -u`. Theo has since sent a commit straight to main at Head Office,
so the student's `main` is behind and the merge will be a real one, on
top of his work. Nothing is tagged anywhere.
"""

from level_helpers import ACT5_BRANCHES, ALL_BRANCHES, THEO, publish, shared_desk

ANCHOR = "tutorial/act5-desk"
WHEN_PLAN = "2025-04-24T09:00:00+00:00"
WHEN_HOURS = "2025-04-24T15:30:00+00:00"
WHEN_THEO = "2025-04-25T07:05:00+00:00"

CLOSE = """# Peak season close-down

- Aisle E overflow racking stays up until the end of May.
- The Fennick Garden Centre returns go back through receiving as normal.
"""

HOURS = """
## Hours

Sunday opening ends after 27 April. Saturday goes back to 07:00 - 11:00.
"""

LAST_ENTRY = "- Dispatch note for 3 March started.\n"
WITH_LAST = LAST_ENTRY + "- Last peak dispatches sent 25 April.\n"


def setup(repo, state):
    # Clears last run's peak-close and peak-2025, here and at Head Office.
    shared_desk(repo, ANCHOR, branches=ALL_BRANCHES + ACT5_BRANCHES)

    # This morning, at Head Office: Theo's last peak entry on main.
    publish(
        repo, ANCHOR,
        [(
            "Log the last peak dispatches",
            THEO,
            WHEN_THEO,
            {"dispatch/log.md": lambda t: t.replace(LAST_ENTRY, WITH_LAST)},
        )],
    )

    # Yesterday: the student's close-down, on its own branch, sent up.
    repo.switch("peak-close", create=True)
    repo.write_file("docs/peak-close.md", CLOSE)
    repo.commit("Write the peak season close-down", date=WHEN_PLAN)
    repo.write_file("docs/peak-close.md", CLOSE + HOURS)
    repo.commit("List the hours going back to normal", date=WHEN_HOURS)
    repo.git("push", "--force", "-u", "origin", "peak-close")
