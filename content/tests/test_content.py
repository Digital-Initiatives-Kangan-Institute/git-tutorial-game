"""The story wraps the real terms; it never replaces them.

Story lines (`story:`, intros, the first hint) may talk about shelves and
crates. Everything a student acts on - a goal's label, a question's prompt,
and every hint after the first - must name the git term, and must not lean
on the picture to do it. These checks keep the warehouse a picture.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from git_tutorial.levels.pack import discover_pack

PACK_ROOT = Path(__file__).resolve().parents[1] / "src" / "git_tutorial_content"
PACK = discover_pack(PACK_ROOT)
LEVELS = [
    PACK.load(entry.id) for entry in PACK.entries
    if (PACK.level_dir(entry.id) / "level.yaml").exists()
]
GLOSSARY = yaml.safe_load((PACK_ROOT / "glossary.yaml").read_text(encoding="utf-8"))
COMMANDS = yaml.safe_load((PACK_ROOT / "commands.yaml").read_text(encoding="utf-8"))

# The picture's words. Fine in a story line; never in an instruction.
METAPHOR = re.compile(
    r"\b(shelf|shelves|crates?|forklift|truck|packing bench|loading floor|back room|the yard)\b",
    re.IGNORECASE,
)

# Words that, in a goal line, show it names something git-specific. Any
# command, glossary term or file path qualifies too.
GIT_WORDS = re.compile(
    r"`[^`]+`|\bgit\b|\b(branch|commit|commits|staged|stage|staging area|working tree|HEAD|"
    r"merge|conflict|stash|reflog|remote|origin|push|pull|fetch|hash|log|status|diff|"
    r"restore|reset|revert|clone|tracked|untracked|ignored|\.gitignore|answer)\b",
    re.IGNORECASE,
)

# A tutorial set in a warehouse must not borrow a real company's name.
REAL_COMPANIES = re.compile(
    r"\b(amazon|tesco|dhl|fedex|ups|walmart|ikea|ocado|sainsbury'?s?|asda|royal mail|"
    r"evri|hermes|maersk|costco|aldi|lidl|argos|b&q|screwfix)\b",
    re.IGNORECASE,
)


def _ids(level: object) -> str:
    return str(getattr(level, "id", ""))


@pytest.mark.parametrize("level", LEVELS, ids=_ids)
def test_every_level_arrives_as_a_job(level) -> None:  # type: ignore[no-untyped-def]
    assert level.job is not None, f"{level.id} has no `job:` ticket"
    assert re.fullmatch(rf"JOB-{level.act}\d\d", level.job.ticket), (
        f"{level.id}: ticket {level.job.ticket!r} should be JOB-{level.act}NN"
    )
    assert level.job.sender and level.job.title


def test_tickets_are_unique() -> None:
    tickets = [level.job.ticket for level in LEVELS if level.job]
    assert len(tickets) == len(set(tickets))


@pytest.mark.parametrize("level", LEVELS, ids=_ids)
def test_every_goal_names_a_git_term(level) -> None:  # type: ignore[no-untyped-def]
    for spec in level.assertions:
        label = str(spec.args.get("label", ""))
        assert label, f"{level.id}: a {spec.kind} goal has no label"
        assert GIT_WORDS.search(label), f"{level.id}: goal {label!r} names no git term"
        assert not METAPHOR.search(label), f"{level.id}: goal {label!r} uses the picture's words"


@pytest.mark.parametrize("level", LEVELS, ids=_ids)
def test_questions_and_later_hints_use_real_terms(level) -> None:  # type: ignore[no-untyped-def]
    for spec in level.assertions:
        prompt = str(spec.args.get("prompt", ""))
        assert not METAPHOR.search(prompt), f"{level.id}: question {prompt!r} uses the picture"
    for rung, hint in enumerate(level.hints[1:], 2):
        found = METAPHOR.search(hint.text)
        assert not found, f"{level.id}: hint {rung} says {found.group(0)!r}; only hint 1 may"


@pytest.mark.parametrize("level", LEVELS, ids=_ids)
def test_every_taught_term_is_in_the_glossary(level) -> None:  # type: ignore[no-untyped-def]
    missing = [term for term in level.teaches if term not in GLOSSARY]
    assert not missing, f"{level.id} teaches {missing}, which the glossary does not define"


def test_every_glossary_entry_points_at_a_real_level() -> None:
    ids = {entry.id for entry in PACK.entries}
    for term, entry in GLOSSARY.items():
        assert entry.get("definition"), f"glossary {term!r} has no definition"
        assert entry.get("level") in ids, f"glossary {term!r} names an unknown level"


def test_the_glossary_says_where_each_command_is_drawn() -> None:
    commands = {str(c["id"]) for c in COMMANDS["commands"] if int(c["tier"]) <= 2}
    for term in commands:
        assert term in GLOSSARY, f"{term!r} is drilled but has no glossary entry"
        assert GLOSSARY[term].get("warehouse"), f"glossary {term!r} has no warehouse line"


def test_no_real_company_is_named() -> None:
    sources = [*PACK_ROOT.rglob("*.md"), *PACK_ROOT.rglob("*.yaml"), *PACK_ROOT.rglob("*.py")]
    for path in sources:
        text = path.read_text(encoding="utf-8")
        found = REAL_COMPANIES.search(text)
        assert not found, f"{path.relative_to(PACK_ROOT)} names {found.group(0)!r}"
