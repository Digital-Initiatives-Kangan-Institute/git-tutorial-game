from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import ClassVar

import pytest

from git_tutorial.cli import build_parser
from git_tutorial.cli.solve import parse_solution

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT.parent / "content" / "src" / "git_tutorial_content"


def _subcommands() -> set[str]:
    sub = next(
        action for action in build_parser()._actions if hasattr(action, "choices")
        and isinstance(getattr(action, "choices", None), dict)
    )
    return set(sub.choices)


class TestTheVerbExists:
    def test_solve_is_a_real_command(self) -> None:
        """Named for the bug: the hint ladder's last rung told a stuck student
        to run `wt solve`, and argparse answered with a usage dump."""
        assert "solve" in _subcommands()

    def test_it_parses_like_the_other_verbs(self) -> None:
        args = build_parser().parse_args(["solve", "--yes"])
        assert args.command == "solve"
        assert args.yes is True


class TestEveryPromisedVerbIsReal:
    """The game tells players what to type. Those must be commands."""

    # `wt on PATH` is doctor's label for a check, and `another wt command is
    # using this repo` is prose. Neither is an instruction to type anything.
    NOT_INSTRUCTIONS: ClassVar[set[str]] = {"on", "command"}

    def _mentions(self) -> dict[str, list[str]]:
        found: dict[str, list[str]] = {}
        sources = [
            *(ROOT / "src").rglob("*.py"),
            ROOT.parent / "play.sh",
            *CONTENT.rglob("*.md"),
            *CONTENT.rglob("*.yaml"),
            *CONTENT.rglob("*.sh"),
        ]
        for path in sources:
            if not path.is_file() or "egg-info" in str(path):
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for verb in re.findall(r"\bwt ([a-z][a-z-]*)", text):
                found.setdefault(verb, []).append(str(path.name))
        return found

    def test_no_text_tells_a_player_to_run_a_command_that_does_not_exist(self) -> None:
        real = _subcommands() | self.NOT_INSTRUCTIONS
        broken = {
            verb: sorted(set(where))
            for verb, where in self._mentions().items()
            if verb not in real
        }
        assert not broken, f"promised to students but not a wt command: {broken}"

    def test_the_scan_actually_finds_things(self) -> None:
        """Guards the regex above: a silent zero-match would make the real
        test vacuous forever."""
        assert "answer" in self._mentions()


class TestParsingASolution:
    def test_steps_split_on_the_marker(self) -> None:
        steps = parse_solution(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            "\n"
            "#: Look at what changed.\n"
            "git status\n"
            "git diff\n"
            "\n"
            "#: Record it.\n"
            "git commit -m 'x'\n"
        )
        assert len(steps) == 2
        assert steps[0].explanation == "Look at what changed."
        assert steps[0].commands == ("git status", "git diff")
        assert steps[1].commands == ("git commit -m 'x'",)

    def test_the_preamble_is_not_a_step(self) -> None:
        """The shebang and `set -euo pipefail` are plumbing, not teaching."""
        steps = parse_solution("#!/usr/bin/env bash\nset -euo pipefail\n#: Go.\ngit status\n")
        assert len(steps) == 1
        assert "set -euo" not in " ".join(steps[0].commands)

    def test_ordinary_comments_are_not_commands(self) -> None:
        steps = parse_solution("#: Go.\n# just a note\ngit status\n")
        assert steps[0].commands == ("git status",)

    def test_a_script_with_no_markers_yields_no_steps(self) -> None:
        assert parse_solution("git status\n") == ()


class TestEveryLevelCanBeExplained:
    def test_each_solution_annotates_itself(self) -> None:
        """`wt solve` narrates from these markers. A script without them runs
        fine in CI and shows the player a blank walkthrough."""
        levels = sorted(CONTENT.rglob("solution.sh"))
        assert levels, "found no solution scripts to check"

        bare = []
        for script in levels:
            steps = parse_solution(script.read_text(encoding="utf-8"))
            if not steps or any(not s.commands for s in steps):
                bare.append(script.parent.name)
        assert not bare, f"solution scripts wt solve cannot narrate: {bare}"


def test_solve_on_a_finished_quest_does_not_crash(tmp_path: Path) -> None:
    """Not a real repo: it must fail the bind cleanly, not raise."""
    from git_tutorial.cli import solve

    args = argparse.Namespace(
        repo=str(tmp_path), levels=None, json=False, debug=False, yes=True
    )
    assert solve.main(args) != 0


def test_a_wrapped_explanation_is_one_step() -> None:
    """Two `#:` lines in a row are a sentence that wrapped in the source, not
    a step with no command. Level 1.7 is written that way."""
    steps = parse_solution(
        "#: Now the file on disk. Doing this first would have copied\n"
        "#: the bad staged version down onto it.\n"
        "git restore docs/getting-started.md\n"
    )
    assert len(steps) == 1
    assert steps[0].explanation.endswith("down onto it.")
    assert steps[0].commands == ("git restore docs/getting-started.md",)
