"""Files one name cannot cover.

The scanner rotates its log, so a rule naming today's files is wrong by
next week. That forces a pattern, which is the transferable part.
"""

ANCHOR = "tutorial/act1-desk"

PAGE = """\
# The handheld scanners

Each scanner writes `scanner.log` in the records folder when it docks.
When the file passes 1 MB it is rotated: the old one becomes
`scanner.log.1`, and so on.

Logs are not cleaned up automatically.
"""

LOG = "06:02 BOOK-IN batch written\n13:47 BOOK-IN batch written\n"


def setup(repo, state):
    repo.require_refs(ANCHOR)
    repo.switch("main", create_if_missing_at=ANCHOR)
    repo.reset_hard(ANCHOR)
    repo.clean(untracked=True, ignored=True)

    repo.write_file("docs/scanner.md", PAGE)
    for suffix in ("", ".1", ".2"):
        repo.write_file(f"scanner.log{suffix}", LOG)
