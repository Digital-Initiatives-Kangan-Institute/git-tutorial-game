from __future__ import annotations

import pytest

from git_tutorial.content.prose import (
    SubstitutionContext,
    TryBlock,
    Verbatim,
    parse_prose,
    substitute,
    to_blocks,
)
from git_tutorial.errors import LevelAuthoringError

pytestmark = pytest.mark.unit

SHAS = {"c02": "7bd01c7aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}


class TestSubstitution:
    def test_sha_and_short(self) -> None:
        ctx = SubstitutionContext(shas=SHAS)
        assert substitute("{{sha:c02}}", ctx) == SHAS["c02"]
        assert substitute("{{short:c02}}", ctx) == "7bd01c7"

    def test_whitespace_inside_the_token_is_tolerated(self) -> None:
        assert substitute("{{ short : c02 }}", SubstitutionContext(shas=SHAS)) == "7bd01c7"

    def test_a_missing_sha_is_an_authoring_error(self) -> None:
        """The manifest is committed, so a miss is a real content bug."""
        with pytest.raises(LevelAuthoringError, match="nope"):
            substitute("{{sha:nope}}", SubstitutionContext(shas=SHAS))

    def test_double_braces_escape(self) -> None:
        assert substitute("{{{{sha:c02}}", SubstitutionContext(shas=SHAS)) == "{{sha:c02}}"

    def test_branch_without_a_snapshot(self) -> None:
        assert substitute("{{branch}}", SubstitutionContext()) == "(unknown)"

    def test_ref_never_raises(self) -> None:
        """Prose must still print in a repo the student has broken."""
        assert substitute("{{ref:rescue}}", SubstitutionContext()) == "rescue"


class TestParsing:
    def test_try_block_collects_its_commands(self) -> None:
        doc = parse_prose("Do this.\n\n  try:  git status\n        git log\n\nAfter.")
        assert doc.try_blocks == (TryBlock(("git status", "git log")),)

    def test_prose_after_a_try_block_is_a_paragraph_again(self) -> None:
        doc = parse_prose("  try:  git status\n\nThen keep reading.")
        assert doc.blocks[-1].text == "Then keep reading."  # type: ignore[union-attr]

    def test_an_empty_try_block_is_an_authoring_error(self) -> None:
        with pytest.raises(LevelAuthoringError, match="at least one command"):
            parse_prose("  try:\n\nnothing")

    def test_no_try_block_is_detectable(self) -> None:
        assert parse_prose("Just prose.").try_blocks == ()

    def test_an_indented_run_keeps_its_own_lines(self) -> None:
        """Numbered questions and command stubs must not be reflowed."""
        doc = parse_prose("Answer these:\n\n  1  Which branch?\n  2  How many commits?\n")
        assert Verbatim(("1  Which branch?", "2  How many commits?")) in doc.blocks


class TestBlocks:
    """The browser receives blocks, never markup it has to trust."""

    def test_every_block_kind_survives(self) -> None:
        source = (
            "# Shift handover\n\n"
            "Marta left you a **note**.\n\n"
            "- check the floor\n\n"
            "    branch = ?\n\n"
            "try:\n    git status\n    git log --oneline\n"
        )
        blocks = to_blocks(parse_prose(source))
        assert [b["type"] for b in blocks] == ["h", "p", "li", "pre", "try"]
        assert blocks[1]["text"] == "Marta left you a **note**."
        assert blocks[3]["lines"] == ["branch = ?"]
        assert blocks[4]["commands"] == ["git status", "git log --oneline"]

    def test_html_is_passed_through_as_text_for_the_page_to_escape(self) -> None:
        blocks = to_blocks(parse_prose("<script>alert(1)</script>"))
        assert blocks == [{"type": "p", "text": "<script>alert(1)</script>"}]

