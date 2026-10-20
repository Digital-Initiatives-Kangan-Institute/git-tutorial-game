from __future__ import annotations

from dataclasses import dataclass, field

FIELD_SEP = "\x1f"

REF_FORMAT = FIELD_SEP.join(
    ("%(objecttype)", "%(refname)", "%(objectname)", "%(*objectname)", "%(upstream)")
)

REF_NAMESPACES = ("refs/heads", "refs/tags", "refs/remotes", "refs/tutorial")


@dataclass(frozen=True, slots=True)
class RefTable:
    branches: dict[str, str] = field(default_factory=dict)
    tags: dict[str, str] = field(default_factory=dict)
    remote_refs: dict[str, str] = field(default_factory=dict)
    tutorial_refs: dict[str, str] = field(default_factory=dict)
    upstream: dict[str, str] = field(default_factory=dict)


def parse_for_each_ref(payload: str) -> RefTable:
    """Parses for-each-ref rows in REF_FORMAT.

    An annotated tag's %(objectname) is the tag object, not the commit, so the
    peeled %(*objectname) wins whenever it is present.
    """
    table = RefTable()
    for line in payload.splitlines():
        if not line:
            continue
        parts = line.split(FIELD_SEP)
        if len(parts) != 5:
            continue
        _objecttype, refname, objectname, peeled, upstream = parts
        sha = peeled or objectname

        if refname.startswith("refs/heads/"):
            name = refname[len("refs/heads/") :]
            table.branches[name] = sha
            if upstream.startswith("refs/remotes/"):
                table.upstream[name] = upstream[len("refs/remotes/") :]
        elif refname.startswith("refs/tags/"):
            table.tags[refname[len("refs/tags/") :]] = sha
        elif refname.startswith("refs/remotes/"):
            table.remote_refs[refname[len("refs/remotes/") :]] = sha
        elif refname.startswith("refs/tutorial/"):
            table.tutorial_refs[refname[len("refs/tutorial/") :]] = sha
    return table
