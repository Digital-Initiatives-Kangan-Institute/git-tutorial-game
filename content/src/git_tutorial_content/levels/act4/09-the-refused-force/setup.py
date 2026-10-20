"""The student rewrote a commit they had already pushed; Ines added to the
same branch at Head Office while they were doing it.

The clone's knowledge of `origin/stocktake-plan` is deliberately left at
the commit the student last saw. A lease that is up to date would let the
force through, and the refusal is the lesson.
"""

from level_helpers import ALL_BRANCHES, INES, shared_desk

ANCHOR = "tutorial/act4-desk"
ACT4_BRANCHES = ("count-b15", "returns-procedure", "shift-report", "stocktake-plan")
WHEN_DRAFT = "2025-03-28T09:30:00+00:00"
WHEN_INES = "2025-03-28T11:10:00+00:00"
WHEN_REWORD = "2025-03-28T11:40:00+00:00"

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

    # Yesterday: drafted and pushed.
    repo.switch("stocktake-plan", create=True)
    repo.write_file("stocktake/plan.md", PLAN)
    draft = repo.commit("Draft the stocktake plan", date=WHEN_DRAFT)
    repo.git("push", "--force", "origin", "stocktake-plan:refs/heads/stocktake-plan")
    repo.git("update-ref", "refs/remotes/origin/stocktake-plan", draft)
    # What `push -u` left behind yesterday. Without it a bare `git push`
    # fails for having no upstream, which is a different lesson.
    repo.git("branch", "--set-upstream-to", "origin/stocktake-plan", "stocktake-plan")

    # Ines, at Head Office, booking the date. Pushed from here for
    # convenience and then wound back out, so the clone never sees it.
    repo.write_file("dispatch/log.md", repo.read("dispatch/log.md").replace(PLANNED, BOOKED))
    repo.commit("Book the stocktake date in the log", date=WHEN_INES, author=INES)
    repo.git("push", "--force", "origin", "HEAD:refs/heads/stocktake-plan")
    repo.reset_hard(draft)
    repo.git("update-ref", "refs/remotes/origin/stocktake-plan", draft)

    # This morning: the student reworded their own commit. Same content,
    # new hash.
    repo.git("reset", "--soft", "HEAD~1")
    repo.commit("Draft the 31 March stocktake plan", date=WHEN_REWORD)
