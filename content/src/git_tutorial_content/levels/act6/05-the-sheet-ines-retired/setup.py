"""A sheet retired at Head Office while the student was editing it.

First, shared history: Marta's opening checks sheet and its README link,
already at Head Office. Then Ines retires the sheet (the checks moved
into Head Office's site handbook) and swaps the README link for a
pointer to the handbook. The student, meanwhile, added a line to the
same sheet and committed it.

The student's pull stops with a modify/delete conflict: "deleted in
<theirs> and modified in HEAD". The right answer is to agree with the
retirement: `git rm` the file, then commit.
"""

from level_helpers import (
    ACT5_BRANCHES,
    ACT6_BRANCHES,
    ALL_BRANCHES,
    INES,
    MARTA,
    diverge_from_head_office,
    shared_desk,
)

ANCHOR = "tutorial/act6-desk"
WHEN_SHEET = "2026-03-16T09:00:00+00:00"
WHEN_INES = "2026-03-25T16:10:00+00:00"
WHEN_MINE = "2026-03-26T07:30:00+00:00"

SHEET = "docs/opening-checks.md"
OPENING = """# Opening checks

Before the first delivery of the day:

    roller doors     open, and the stops are down
    dock leveller    test it with nothing on it
    scanners         charged, and logged in

Write any fault in the dispatch log.
"""
SCANNERS = "    scanners         charged, and logged in\n"
FIRST_AID = "    first-aid box    seal intact, nothing used\n"

LINK = "- [Opening checks](docs/opening-checks.md)\n"
HANDBOOK = "- Opening checks: see the Head Office site handbook\n"


def setup(repo, state):
    shared_desk(repo, ANCHOR, branches=ALL_BRANCHES + ACT5_BRANCHES + ACT6_BRANCHES)

    # Shared history: the sheet both sides start from, already at Head Office.
    repo.write_file(SHEET, OPENING)
    repo.write_file("README.md", repo.read("README.md") + LINK)
    base = repo.commit("Write up the opening checks", date=WHEN_SHEET, author=MARTA)
    repo.git("push", "--force", "origin", "HEAD:refs/heads/main")

    diverge_from_head_office(
        repo,
        base,
        theirs=[(
            "Retire the opening checks sheet", INES, WHEN_INES,
            {SHEET: None, "README.md": lambda t: t.replace(LINK, HANDBOOK)},
        )],
        ours=[(
            "Add the first-aid box to the opening checks", None, WHEN_MINE,
            {SHEET: lambda t: t.replace(SCANNERS, SCANNERS + FIRST_AID)},
        )],
    )
