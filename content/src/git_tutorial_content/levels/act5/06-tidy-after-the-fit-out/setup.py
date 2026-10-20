"""The aisle E fit-out branch is finished. The student wrote it over two
days and pushed it with `push -u`; Head Office has `aisle-e-fitout`, and
the student is still on it.

Nobody has merged it. This time the student folds it in themselves, sends
`main` up, and only then clears the branch away in both places. Deleting
first would leave the fit-out notes on no branch at all, which the goals
catch: `main` here and at Head Office must hold the work.
"""

from level_helpers import ACT5_BRANCHES, ALL_BRANCHES, shared_desk

ANCHOR = "tutorial/act5-desk"
WHEN_PLAN = "2025-04-10T08:40:00+00:00"
WHEN_DATE = "2025-04-11T13:15:00+00:00"

PLAN = """# Aisle E fit-out

New racking for the Easter overflow, four bays high.

- Bays E-01 to E-06: pallet wrap and cartons
- Bays E-07 to E-10: garden centre returns
"""

DELIVERY = """
Racking delivered by Kestrelby on 11 April. Fitted and load-checked.
"""


def setup(repo, state):
    # Clears last run's aisle-e-fitout here and at Head Office.
    shared_desk(repo, ANCHOR, branches=ALL_BRANCHES + ACT5_BRANCHES)

    repo.switch("aisle-e-fitout", create=True)
    repo.write_file("docs/aisle-e-fitout.md", PLAN)
    repo.commit("Plan the aisle E fit-out", date=WHEN_PLAN)
    repo.write_file("docs/aisle-e-fitout.md", PLAN + DELIVERY)
    repo.commit("Record the aisle E racking delivery", date=WHEN_DATE)
    repo.git("push", "--force", "-u", "origin", "aisle-e-fitout")
