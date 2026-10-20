"""Yesterday's force push, already done.

The student fetched Ines's commit and then forced over it, which is the one
sequence `--force-with-lease` cannot save anybody from: the lease was
satisfied, because they really had seen the commit they replaced.

Setup leaves the wreckage and the evidence: Head Office no longer has her
commit, and the clone's `origin/stocktake-plan` reflog still does.
"""

from level_helpers import ALL_BRANCHES, INES, shared_desk

ANCHOR = "tutorial/act4-desk"
ACT4_BRANCHES = ("count-b15", "returns-procedure", "shift-report", "stocktake-plan")
WHEN_DRAFT = "2025-03-29T09:15:00+00:00"
WHEN_INES = "2025-03-29T10:40:00+00:00"
WHEN_REWORD = "2025-03-29T11:05:00+00:00"

PLAN = """# Stocktake plan

- Close receiving at 12:00 the day before.
- Count aisle B first, then aisle D.
- Theo signs off each aisle before the next one starts.
"""

PLANNED = "Stocktake is planned for the end of the month.\n"
BOOKED = "Stocktake is booked for Monday 31 March.\n"


def setup(repo, state):
    # Clears the last run's stocktake-plan here and at Head Office.
    shared_desk(repo, ANCHOR, branches=ALL_BRANCHES + ACT4_BRANCHES)

    repo.switch("stocktake-plan", create=True)
    repo.write_file("stocktake/plan.md", PLAN)
    draft = repo.commit("Draft the stocktake plan", date=WHEN_DRAFT)
    repo.git("push", "--force", "origin", "stocktake-plan:refs/heads/stocktake-plan")
    repo.git("branch", "--set-upstream-to", "origin/stocktake-plan", "stocktake-plan")

    # Ines's commit, pushed to Head Office and then fetched - so the clone
    # has both the object and a reflog entry saying where it came from.
    # That entry is the only record left after the force.
    repo.write_file("dispatch/log.md", repo.read("dispatch/log.md").replace(PLANNED, BOOKED))
    repo.commit("Book the stocktake date in the log", date=WHEN_INES, author=INES)
    repo.git("push", "--force", "origin", "HEAD:refs/heads/stocktake-plan")
    repo.reset_hard(draft)
    # Wind the clone's knowledge back and then fetch for real, so the
    # reflog entry reads `fetch` rather than `update by push`.
    repo.git("update-ref", "refs/remotes/origin/stocktake-plan", draft)
    repo.git("fetch", "origin")

    # Then the rewording, and the force that landed because the lease was
    # satisfied: the student had seen her commit, and replaced it anyway.
    repo.git("reset", "--soft", "HEAD~1")
    repo.commit("Draft the 31 March stocktake plan", date=WHEN_REWORD)
    repo.git("push", "--force-with-lease", "origin", "stocktake-plan:refs/heads/stocktake-plan")
    repo.git("fetch", "origin")
