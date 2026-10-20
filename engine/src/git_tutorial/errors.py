from __future__ import annotations


class TutorialError(Exception):
    """Base for everything this package raises."""


class GitCommandError(TutorialError):
    def __init__(self, argv: tuple[str, ...], returncode: int, stderr: str) -> None:
        self.argv = argv
        self.returncode = returncode
        self.stderr = stderr
        super().__init__(f"git {' '.join(argv)} exited {returncode}: {stderr.strip()}")


class RepoNotFound(TutorialError):
    pass


class RefResolutionError(TutorialError):
    """A commit-ref in a level definition did not resolve.

    Per spec 6.2 this is a level authoring error, never a student failure, and
    must be surfaced distinctly from a failed assertion.
    """


class LevelAuthoringError(TutorialError):
    pass


class StateCorruptError(TutorialError):
    pass
