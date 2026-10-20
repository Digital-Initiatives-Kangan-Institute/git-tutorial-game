"""One file, changed twice, staged in between.

This is the shape where the three copies stop being a diagram: commit,
staging area and working tree each hold a different version, and
undoing in the wrong order silently keeps the wrong one.
"""

ANCHOR = "tutorial/act1-desk"


def setup(repo, state):
    repo.require_refs(ANCHOR)
    repo.switch("main", create_if_missing_at=ANCHOR)
    repo.reset_hard(ANCHOR)
    repo.clean(untracked=True, ignored=True)

    page = repo.read("docs/receiving.md")

    # First edit, then staged.
    repo.write_file(
        "docs/receiving.md",
        page.rstrip("\n") + "\n\nNote: the BOOK-IN scanner is probably faulty.\n",
    )
    repo.git("add", "docs/receiving.md")

    # Second edit, left on disk. Worse, and unchecked.
    staged = repo.read("docs/receiving.md")
    repo.write_file(
        "docs/receiving.md",
        staged.rstrip("\n") + "\nActually it is definitely faulty.\n",
    )
