"""Shared setup helpers.

The pack root is put on sys.path while a setup script runs, so every level
can `from level_helpers import ...`.
"""

# Every branch (job bay) any Act 2 level opens. A setup that deletes only
# its own leaves the previous level's behind, and they pile up in the
# student's graph for the rest of the act.
ACT2_BRANCHES = (
    "aisle-b-count",
    "aisle-d-fitout",
    "aisle-d-signoff",
    "racking-checks",
    "recount-b14",
    "stocktake-prep",
    "typo-fix",
)

# Act 3 fabricates its own incidents, and each one leaves wreckage with a
# name. Clearing them all keeps the previous incident's rescue out of the
# picture: in an act about recovery, a rescue the student did not make is
# actively misleading.
ACT3_BRANCHES = (
    "fennick-note",
    "hotfix",
    "month-end",
)

# Act 3 clears Act 2's bays too: a student playing straight through arrives
# from 2.12 with that act's last branches still standing.
# Act 4's own branches, so Act 5 does not inherit them from 4.11.
ACT4_BRANCHES = ("count-b15", "returns-procedure", "shift-report", "stocktake-plan")

ALL_BRANCHES = tuple(sorted(set(ACT2_BRANCHES) | set(ACT3_BRANCHES) | set(ACT4_BRANCHES)))

# Every branch any Act 5 level creates, locally or at Head Office.
ACT5_BRANCHES = (
    "aisle-c-count",
    "aisle-e-fitout",
    "april-returns",
    "april-slots",
    "easter-hours",
    "fennick-order",
    "pallet-audit",
    "peak-close",
    "peak-rota",
)

# Every branch any Act 6 level creates. Act 6 setups clear all earlier
# acts' branches too: ALL_BRANCHES + ACT5_BRANCHES + ACT6_BRANCHES.
ACT6_BRANCHES = ()


def fresh_desk(repo, anchor, *, branches=ACT2_BRANCHES):
    """The idempotent preamble for a level that works with branches.

    Abandon any paused merge, discard changes, clear the stash, and only
    then move to main: a level cannot switch while its own last run left a
    conflict or a modified file that does not exist on main.
    """
    repo.require_refs(anchor)
    repo.git("merge", "--abort", check=False)
    repo.git("reset", "--hard")
    repo.clean(untracked=True, ignored=True)
    repo.git("stash", "clear")
    repo.switch("main", create_if_missing_at=anchor)
    repo.reset_hard(anchor)
    repo.clean(untracked=True, ignored=True)
    for name in branches:
        repo.delete_branch(name, force=True)


# The people whose records the student works alongside. Their commits are
# made with these names, so `git log` reads like a team's history.
MARTA = ("Marta Vos", "marta.vos@tallowmere.example")  # warehouse manager
THEO = ("Theo Banda", "theo.banda@tallowmere.example")  # stock controller
INES = ("Ines Calder", "ines.calder@tallowmere.example")  # Head Office buyer


def shared_desk(repo, anchor, *, branches=ALL_BRANCHES):
    """`fresh_desk`, plus Head Office: the repository `origin` points at.

    Act 4's levels are about what somebody else has sent to Head Office, so
    the remote is part of the starting state and has to be reset like the
    rest. Head Office lives in ~/.gittutorial and outlives every workspace,
    so a level that pushed something last run would otherwise hand the next
    run a repository nobody designed.

    The local `origin/main` is put back by hand afterwards. Pushing updates
    it, and a level that means to say "Head Office has moved on and you do
    not know yet" needs the student's knowledge to be stale.
    """
    fresh_desk(repo, anchor, branches=branches)

    repo.git("push", "--force", "origin", f"{anchor}:refs/heads/main")
    for line in repo.git("ls-remote", "--heads", "origin").stdout.splitlines():
        name = line.partition("refs/heads/")[2].strip()
        if name and name != "main":
            repo.git("push", "origin", "--delete", name, check=False)

    # Tags are seals that outlive branches: clear them on both sides, or a
    # seal from a previous job turns up on a crate this job never made.
    for line in repo.git("ls-remote", "--tags", "origin").stdout.splitlines():
        name = line.partition("refs/tags/")[2].strip()
        if name and not name.endswith("^{}"):
            repo.git("push", "origin", "--delete", f"refs/tags/{name}", check=False)
    for name in repo.git("tag", "--list").stdout.split():
        repo.git("tag", "-d", name)

    repo.git("fetch", "--prune", "origin", check=False)
    repo.git("update-ref", "refs/remotes/origin/main", anchor)


def publish(repo, anchor, commits, *, branch="main"):
    """Commits made by somebody else, already at Head Office.

    Made locally, pushed, and then wound back out of the student's own
    repository: Head Office keeps them, the workspace does not, and
    `origin/main` is left saying what it said before. That is exactly the
    state a student is in when a colleague sends records up at lunch.

    `commits` is a sequence of (message, author, date, edits) where `edits`
    maps a path to new text, or to a function of the current text.
    """
    for message, author, date, edits in commits:
        for path, change in edits.items():
            repo.write_file(path, change(repo.read(path)) if callable(change) else change)
        repo.commit(message, date=date, author=author)

    repo.git("push", "--force", "origin", f"HEAD:refs/heads/{branch}")
    repo.reset_hard(anchor)
    repo.clean(untracked=True, ignored=True)

    # The push taught the workspace about its own handiwork. Put its
    # knowledge back: main as it stood, and no trace of a branch the
    # student is supposed to discover by fetching.
    if branch == "main":
        repo.git("update-ref", "refs/remotes/origin/main", anchor)
    else:
        repo.git("update-ref", "-d", f"refs/remotes/origin/{branch}", check=False)


def delete_at_head_office(repo, *names):
    """Branches somebody else deleted at Head Office, which this workspace
    has not heard about: the `origin/<name>` notes stay until the student
    runs `git fetch --prune`."""
    for name in names:
        kept = repo.git("rev-parse", "--verify", "-q", f"refs/remotes/origin/{name}",
                        check=False).stdout.strip()
        repo.git("push", "origin", "--delete", name, check=False)
        if kept:
            repo.git("update-ref", f"refs/remotes/origin/{name}", kept)


def merge_at_head_office(repo, anchor, branch, *, message, author, date):
    """A colleague merges `branch` into main at Head Office.

    Done in this workspace and then wound back, like `publish`: Head Office
    has the merge, and the student's `main` and `origin/main` still say what
    they said before, until they fetch or pull.
    """
    repo.switch("main")
    repo.git("merge", "--no-ff", "--no-edit", "-m", message, branch,
             _env={
                 "GIT_AUTHOR_NAME": author[0], "GIT_AUTHOR_EMAIL": author[1],
                 "GIT_COMMITTER_NAME": author[0], "GIT_COMMITTER_EMAIL": author[1],
                 "GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date,
             })
    repo.git("push", "origin", "HEAD:refs/heads/main")
    repo.reset_hard(anchor)
    repo.git("update-ref", "refs/remotes/origin/main", anchor)


def diverge_from_head_office(repo, anchor, *, theirs, ours):
    """Head Office and the workspace each move on from `anchor`, so the
    student's next `git pull` meets real disagreement.

    `theirs` and `ours` are sequences of (message, author, date, edits), as in
    `publish`; in `edits`, a value of None deletes the file. Theirs go to
    Head Office only; ours are committed in the workspace, on main.
    """
    def apply(commits):
        for message, author, date, edits in commits:
            for path, change in edits.items():
                if change is None:
                    repo.git("rm", "-q", "--", path)
                    continue
                repo.write_file(path, change(repo.read(path)) if callable(change) else change)
                repo.git("add", "--", path)
            repo.commit(message, date=date, author=author)

    apply(theirs)
    repo.git("push", "--force", "origin", "HEAD:refs/heads/main")
    repo.reset_hard(anchor)
    repo.clean(untracked=True, ignored=True)
    repo.git("update-ref", "refs/remotes/origin/main", anchor)
    apply(ours)

