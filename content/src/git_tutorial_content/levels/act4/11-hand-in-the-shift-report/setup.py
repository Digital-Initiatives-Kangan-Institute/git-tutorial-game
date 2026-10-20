"""The last level: the student's rough notes are on disk, untracked, and
the report they turn into is the thing to hand in.

The scratch file is what makes `.gitignore` earn its place here. Without
it, `git add .` would be harmless, and there would be nothing to keep out.
"""

from level_helpers import ALL_BRANCHES, shared_desk

ANCHOR = "tutorial/act4-desk"
ACT4_BRANCHES = ("count-b15", "returns-procedure", "shift-report", "stocktake-plan")

SCRATCH = """rough notes, not for filing

mon  read the handover. 10 commits, Theo last
tue  B-15 = 12 bundles? recount before telling Ines
wed  Head Office refused my push. pull first, then push
thu  finished Ines's returns sentence on her branch
fri  force-with-lease said stale info. fetch and look
"""


def setup(repo, state):
    # Clears the last run's shift-report here and at Head Office, and
    # cleans untracked files, so the notes below are written fresh.
    shared_desk(repo, ANCHOR, branches=ALL_BRANCHES + ACT4_BRANCHES)
    repo.write_file("scratch.txt", SCRATCH)
