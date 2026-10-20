"""Marta asked for the week ending 21 March to be sealed: Theo's commit
"Log the week's dispatches" (the act's anchor, c10). Ines sent two April
commits up after it, the student pulled them, and then typed
`git tag dispatch-21-march` with no hash, which sealed HEAD.

So the wrong tag is real and local-only: `shared_desk` cleared every tag
at Head Office, and nothing here pushes this one. `main` is in step with
Head Office, so the job is the tag and only the tag.
"""

from level_helpers import ACT5_BRANCHES, ALL_BRANCHES, INES, shared_desk

ANCHOR = "tutorial/act5-desk"
WHEN_SLOTS = "2025-04-14T08:10:00+00:00"
WHEN_PRICE = "2025-04-14T09:25:00+00:00"

SLOTS = """# April delivery slots

    Kestrelby Packaging   Tuesday and Thursday, 07:00
    Fennick returns       Friday, 13:00
"""

HOLD = "Prices hold until 31 March."
NEW_HOLD = "April prices agreed on 14 April; the old list no longer holds."


def setup(repo, state):
    shared_desk(repo, ANCHOR, branches=ALL_BRANCHES + ACT5_BRANCHES)

    # Ines's April work, at Head Office and already pulled.
    repo.write_file("dispatch/april-slots.md", SLOTS)
    repo.commit("Add the April delivery slots", date=WHEN_SLOTS, author=INES)
    repo.write_file(
        "suppliers/price-list.md", repo.read("suppliers/price-list.md").replace(HOLD, NEW_HOLD)
    )
    repo.commit("Agree the April prices", date=WHEN_PRICE, author=INES)
    repo.git("push", "--force", "origin", "main")
    repo.git("fetch", "origin")

    # The student's mistake: a tag on HEAD, not on the week's log.
    repo.tag("dispatch-21-march")
