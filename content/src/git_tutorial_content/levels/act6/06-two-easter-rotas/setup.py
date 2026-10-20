"""Two people wrote the same new file.

Neither `rota/easter.md` existed at the anchor. Theo wrote one covering
Good Friday and the Saturday and sent it up; the student wrote one
covering Easter Monday and the Tuesday and committed it. The pull stops
with an add/add conflict ("added by both"): there is no common version,
so the markers fence off the two drafts' differing lines.

Both halves are needed. The answer is a hand-merge holding all four days.
"""

from level_helpers import (
    ACT5_BRANCHES,
    ACT6_BRANCHES,
    ALL_BRANCHES,
    THEO,
    diverge_from_head_office,
    shared_desk,
)

ANCHOR = "tutorial/act6-desk"
WHEN_THEO = "2026-03-26T10:15:00+00:00"
WHEN_MINE = "2026-03-26T10:40:00+00:00"

ROTA = "rota/easter.md"
THEO_ROTA = """# Easter rota

- Good Friday 3 April: Theo and Ines
- Saturday 4 April: Theo
"""
MY_ROTA = """# Easter rota

- Easter Monday 6 April: Marta and the trainee
- Tuesday 7 April: the trainee
"""


def setup(repo, state):
    shared_desk(repo, ANCHOR, branches=ALL_BRANCHES + ACT5_BRANCHES + ACT6_BRANCHES)

    diverge_from_head_office(
        repo,
        ANCHOR,
        theirs=[("Draft the Easter rota", THEO, WHEN_THEO, {ROTA: THEO_ROTA})],
        ours=[("Write the Easter rota", None, WHEN_MINE, {ROTA: MY_ROTA})],
    )
