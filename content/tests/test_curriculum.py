"""The budget and coverage lints.

These check the curriculum rather than the code: that no level introduces too
much at once, and that every command a student will actually use is practised
three times, spaced apart.

Failures name the command, its count and the levels involved. A bare
assertion is useless to someone rebalancing a curriculum.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import pytest
import yaml

from git_tutorial.levels.pack import discover_pack

PACK_ROOT = Path(__file__).resolve().parents[1] / "src" / "git_tutorial_content"
PACK = discover_pack(PACK_ROOT)

# Teaching counts as the first performance.
REQUIRED_PERFORMANCES = 3

# Drilled tiers. Tier 3 is recognise-only and must not be drilled.
DRILLED_TIERS = (1, 2)

# Acts whose taught commands the three-times rule applies to. Every act
# the pack contains: an act added later must not quietly escape the rule
# by not being listed here, which is what happened when act 3 arrived and
# its own three commands went unchecked.
DRILLED_ACTS = tuple(sorted({entry.act for entry in PACK.entries}))


@dataclass(frozen=True)
class Vocabulary:
    tier: dict[str, int]
    canonical: dict[str, str]  # alias or id -> canonical id
    cut: tuple[str, ...]
    deferred: dict[str, str] = field(default_factory=dict)  # id -> reason
    exempt: dict[str, str] = field(default_factory=dict)  # id -> reason

    def resolve(self, name: str) -> str | None:
        return self.canonical.get(name.strip())


def load_vocabulary() -> Vocabulary:
    raw = yaml.safe_load((PACK_ROOT / "commands.yaml").read_text(encoding="utf-8"))
    tier: dict[str, int] = {}
    canonical: dict[str, str] = {}
    for entry in raw["commands"]:
        name = str(entry["id"])
        tier[name] = int(entry["tier"])
        canonical[name] = name
        for alias in entry.get("aliases") or []:
            canonical[str(alias)] = name
    deferred = {k: v.get("why", "") for k, v in (raw.get("deferred") or {}).items()}
    exempt = {k: v.get("why", "") for k, v in (raw.get("exempt") or {}).items()}
    return Vocabulary(tier=tier, canonical=canonical, cut=tuple(raw.get("cut") or ()),
                      deferred=deferred, exempt=exempt)


VOCAB = load_vocabulary()
LEVELS = [
    PACK.load(entry.id) for entry in PACK.entries
    if (PACK.level_dir(entry.id) / "level.yaml").exists()
]


def complete_acts() -> set[int]:
    """Acts declared finished in the manifest.

    The coverage rule binds per act, as each is completed. A half-built act
    cannot satisfy a three-times rule, and a suite that is permanently red
    stops telling anyone anything.
    """
    raw = yaml.safe_load((PACK_ROOT / "manifest.yaml").read_text(encoding="utf-8"))
    return {
        int(act["act"]) for act in raw.get("acts") or [] if act.get("complete", False)
    }


COMPLETE_ACTS = complete_acts()


def performances() -> dict[str, list[str]]:
    """Canonical command id -> the level ids that perform it, in play order."""
    out: dict[str, list[str]] = {}
    for level in LEVELS:
        for name in (*level.teaches, *level.reuses):
            key = VOCAB.resolve(name)
            if key is not None:
                out.setdefault(key, []).append(level.id)
    return out


def taught_in_drilled_acts() -> dict[str, tuple[str, int]]:
    """Canonical id -> (the level that teaches it, that level's act)."""
    out: dict[str, tuple[str, int]] = {}
    for level in LEVELS:
        if level.act not in DRILLED_ACTS:
            continue
        for name in level.teaches:
            key = VOCAB.resolve(name)
            if key is not None:
                out[key] = (level.id, level.act)
    return out


def is_spaced(level_ids: list[str]) -> bool:
    """Practice must be spread out, not crammed.

    Only commands sitting at the bare minimum are policed. A command used
    in more levels than the minimum is being practised throughout the act
    — `status` appears in all nine Act 1 levels — and demanding a gap in
    that case would flag the best-covered commands in the game.
    """
    order = {entry.id: i for i, entry in enumerate(PACK.entries)}
    positions = sorted(order[level_id] for level_id in level_ids if level_id in order)
    if len(positions) < REQUIRED_PERFORMANCES:
        return False
    if len(positions) > REQUIRED_PERFORMANCES:
        return True
    # Exactly the minimum: at least one level between first and last must
    # not use it, or this is three in a row and then never again.
    span = positions[-1] - positions[0] + 1
    return span > len(positions)


class TestBudget:
    """Spec 3.2: at most two new commands per level, at least two reused."""

    @pytest.mark.parametrize("level", LEVELS, ids=lambda level: level.id)
    def test_at_most_two_new_commands(self, level) -> None:  # type: ignore[no-untyped-def]
        if level.budget_exception:
            pytest.skip(f"documented exception: {level.budget_exception}")
        assert len(level.teaches) <= 2, (
            f"{level.id} teaches {len(level.teaches)} commands "
            f"({', '.join(level.teaches)}). A self-paced student has no one to "
            "unblock them, so three new things is three independent failure "
            "points. Split the level, or declare a budget_exception saying why."
        )

    @pytest.mark.parametrize("level", LEVELS, ids=lambda level: level.id)
    def test_at_least_two_reused(self, level) -> None:  # type: ignore[no-untyped-def]
        if level.budget_exception:
            pytest.skip(f"documented exception: {level.budget_exception}")
        assert len(level.reuses) >= 2, (
            f"{level.id} reuses {len(level.reuses)} commands. Spaced reuse is "
            "doing more work here than any individual level."
        )

    @pytest.mark.parametrize("level", LEVELS, ids=lambda level: level.id)
    def test_every_named_command_is_in_the_vocabulary(self, level) -> None:  # type: ignore[no-untyped-def]
        unknown = [
            name for name in (*level.teaches, *level.reuses)
            if VOCAB.resolve(name) is None
        ]
        assert not unknown, (
            f"{level.id} names {unknown}, which is not in commands.yaml. "
            "Either it is a typo or the vocabulary needs the entry."
        )

    def test_nothing_is_taught_twice(self) -> None:
        seen: dict[str, str] = {}
        clashes: list[str] = []
        for level in LEVELS:
            for name in level.teaches:
                key = VOCAB.resolve(name) or name
                if key in seen:
                    clashes.append(f"{key}: taught in both {seen[key]} and {level.id}")
                seen[key] = level.id
        assert not clashes, "a second teach is a reuse:\n  " + "\n  ".join(clashes)

    def test_nothing_is_reused_before_it_is_taught(self) -> None:
        order = {entry.id: i for i, entry in enumerate(PACK.entries)}
        taught_at: dict[str, int] = {}
        for level in LEVELS:
            for name in level.teaches:
                key = VOCAB.resolve(name) or name
                taught_at.setdefault(key, order[level.id])

        problems: list[str] = []
        for level in LEVELS:
            for name in level.reuses:
                key = VOCAB.resolve(name) or name
                first = taught_at.get(key)
                if first is None:
                    problems.append(f"{level.id} reuses {key}, which is never taught")
                elif first >= order[level.id]:
                    problems.append(
                        f"{level.id} reuses {key}, but it is not taught until later"
                    )
        assert not problems, "you cannot reuse what has not been taught:\n  " + \
            "\n  ".join(problems)


class TestCoverage:
    """The three-times rule: every drilled command, three spaced levels."""

    def test_the_coverage_table(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Prints the table on every run — it is the artifact the curriculum
        is maintained against, not just a failure message."""
        seen = performances()
        taught = taught_in_drilled_acts()

        rows: list[str] = []
        problems: list[str] = []

        for command, (level_id, act) in sorted(taught.items()):
            tier = VOCAB.tier.get(command, 0)
            if tier not in DRILLED_TIERS:
                continue
            where = seen.get(command, [])
            deferred = VOCAB.deferred.get(command)
            count = len(where)
            binding = act in COMPLETE_ACTS

            if command in VOCAB.exempt:
                mark = "exempt"
            elif deferred and count >= REQUIRED_PERFORMANCES - 1:
                mark = "defer"
            elif count < REQUIRED_PERFORMANCES:
                mark = "SHORT" if binding else "building"
                if binding:
                    problems.append(
                        f"{command}: performed {count}x, needs {REQUIRED_PERFORMANCES}. "
                        f"Taught in {level_id}; also in "
                        f"{', '.join(w for w in where if w != level_id) or 'nothing else'}."
                    )
            elif not is_spaced(where):
                mark = "BUNCHED" if binding else "building"
                if binding:
                    problems.append(
                        f"{command}: performed {count}x but all within consecutive "
                        f"levels ({', '.join(where)}). Put other material between them."
                    )
            else:
                mark = "ok"
            rows.append(f"  {mark:8} t{tier}  {command:24} {count}x  {', '.join(where)}")

        building = sorted(set(DRILLED_ACTS) - COMPLETE_ACTS)
        with capsys.disabled():
            span = f"{DRILLED_ACTS[0]}-{DRILLED_ACTS[-1]}" if DRILLED_ACTS else "none"
            print(f"\n\n  coverage — every tier 1/2 command taught in acts {span}\n")
            print("\n".join(rows) or "  (no levels yet)")
            if building:
                print(
                    f"\n  act(s) {building} are still being built, so their commands are "
                    "\n  reported but not enforced. Set `complete: true` in manifest.yaml"
                    "\n  when an act is finished and the rule starts biting."
                )
            print()

        assert not problems, "\n  " + "\n  ".join(problems)

    def test_tier_three_is_never_drilled(self) -> None:
        """Spec 3.1: recognise, do not drill."""
        seen = performances()
        overdone = [
            f"{command} appears in {len(where)} levels ({', '.join(where)})"
            for command, where in seen.items()
            if VOCAB.tier.get(command) == 3 and len(where) > 2
        ]
        assert not overdone, (
            "tier 3 is recognise-only; drilling it teaches beginners to reach "
            "for tools they cannot yet reason about:\n  " + "\n  ".join(overdone)
        )

    def test_cut_commands_appear_nowhere(self) -> None:
        """Including in prose and solution scripts, not just the metadata."""
        offenders: list[str] = []
        for entry in PACK.entries:
            for path in (PACK.root / entry.rel_path).rglob("*"):
                if path.suffix not in (".yaml", ".md", ".sh"):
                    continue
                text = path.read_text(encoding="utf-8")
                for command in VOCAB.cut:
                    if re.search(rf"\bgit {re.escape(command)}\b", text):
                        offenders.append(f"{path.relative_to(PACK.root)}: git {command}")
        assert not offenders, (
            "these are cut from the curriculum on purpose:\n  " + "\n  ".join(offenders)
        )

    def test_a_deferral_is_declared_not_assumed(self) -> None:
        """Anything short of three performances must say so in commands.yaml,
        with a reason, rather than quietly failing to be drilled."""
        for command, reason in VOCAB.deferred.items():
            assert command in VOCAB.tier, f"{command} is deferred but not in the vocabulary"
            assert reason.strip(), f"{command} is deferred with no reason given"

        for command, reason in VOCAB.exempt.items():
            assert command in VOCAB.tier, f"{command} is exempt but not in the vocabulary"
            assert reason.strip(), f"{command} is exempt with no reason given"
            assert command not in VOCAB.deferred, (
                f"{command} is both deferred and exempt — say which"
            )
