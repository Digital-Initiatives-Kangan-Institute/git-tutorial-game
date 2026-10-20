"""Two sheets retired at Head Office, and a scratch file on the books.

Shared history first: Theo's sheets for the aisle E overflow racking and
the seasonal twine, already at Head Office. Then Ines retires both (the
racking is down, the twine is discontinued). The student, meanwhile,
counted both and committed, and the same commit swept in the scanner's
scratch dump, stocktake.tmp, which was never meant to be tracked.

The pull stops with two modify/delete conflicts. The student takes both
sheets off the books with `git rm`, stops tracking the scratch file with
`git rm --cached` (it stays on disk), and ignores it in .gitignore.
"""

from level_helpers import (
    ACT5_BRANCHES,
    ACT6_BRANCHES,
    ALL_BRANCHES,
    INES,
    THEO,
    diverge_from_head_office,
    shared_desk,
)

ANCHOR = "tutorial/act6-desk"
WHEN_SHEETS = "2026-03-17T11:00:00+00:00"
WHEN_INES = "2026-03-26T16:30:00+00:00"
WHEN_MINE = "2026-03-27T08:20:00+00:00"

OVERFLOW = "stock/aisle-e-overflow.md"
TWINE = "stock/seasonal-twine.md"
SCRATCH = "stocktake.tmp"

OVERFLOW_SHEET = """# Aisle E overflow

**E-01 Cartons, double wall**

Not counted yet.
"""
TWINE_SHEET = """# Seasonal twine

**T-02 Garden twine, green**

Not counted yet.
"""
SCAN_DUMP = """SCAN 2026-03-27 08:02 E-01 x14
SCAN 2026-03-27 08:09 T-02 x9
SCAN 2026-03-27 08:11 T-02 x-1 VOID
"""


def setup(repo, state):
    shared_desk(repo, ANCHOR, branches=ALL_BRANCHES + ACT5_BRANCHES + ACT6_BRANCHES)

    # Shared history: both sheets, already at Head Office.
    repo.write_file(OVERFLOW, OVERFLOW_SHEET)
    repo.write_file(TWINE, TWINE_SHEET)
    base = repo.commit("Start the overflow and twine sheets", date=WHEN_SHEETS, author=THEO)
    repo.git("push", "--force", "origin", "HEAD:refs/heads/main")

    diverge_from_head_office(
        repo,
        base,
        theirs=[(
            "Retire the overflow and twine sheets", INES, WHEN_INES,
            {OVERFLOW: None, TWINE: None},
        )],
        ours=[(
            "Count the overflow and twine stock", None, WHEN_MINE,
            {
                OVERFLOW: lambda t: t.replace("Not counted yet.", "14 bundles counted."),
                TWINE: lambda t: t.replace("Not counted yet.", "8 balls counted."),
                SCRATCH: SCAN_DUMP,
            },
        )],
    )
