from __future__ import annotations

from dataclasses import dataclass, field

# A developer's global gitconfig leaking into a fixture is the single most
# likely source of "passes locally, fails in CI" in this project, so every
# input to a commit sha is pinned explicitly.
FIXED_NAME = "Tutorial Fixture"
FIXED_EMAIL = "fixture@git-tutorial.invalid"
EPOCH = 1704067200  # 2024-01-01T00:00:00+0000
STEP_SECONDS = 60

CONFIG_ARGS: tuple[str, ...] = (
    "-c", "core.autocrlf=false",
    "-c", "core.eol=lf",
    "-c", "gc.auto=0",
    "-c", "commit.gpgsign=false",
    "-c", "tag.gpgsign=false",
    "-c", "init.defaultBranch=main",
    "-c", "advice.detachedHead=false",
    "-c", "protocol.file.allow=always",
)


def base_env(home: str) -> dict[str, str]:
    return {
        "HOME": home,
        "USERPROFILE": home,
        "XDG_CONFIG_HOME": home,
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_SYSTEM": "/dev/null",
        "GIT_AUTHOR_NAME": FIXED_NAME,
        "GIT_AUTHOR_EMAIL": FIXED_EMAIL,
        "GIT_COMMITTER_NAME": FIXED_NAME,
        "GIT_COMMITTER_EMAIL": FIXED_EMAIL,
    }


@dataclass
class FixedClock:
    """Advances a fixed amount per commit so shas are reproducible."""

    seconds: int = EPOCH
    step: int = STEP_SECONDS
    tz: str = "+0000"
    issued: list[str] = field(default_factory=list)

    def next_date(self) -> str:
        stamp = f"{self.seconds} {self.tz}"
        self.issued.append(stamp)
        self.seconds += self.step
        return stamp

    def date_env(self) -> dict[str, str]:
        stamp = self.next_date()
        return {"GIT_AUTHOR_DATE": stamp, "GIT_COMMITTER_DATE": stamp}
