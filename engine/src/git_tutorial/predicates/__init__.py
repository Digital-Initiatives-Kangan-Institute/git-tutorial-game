"""Predicate registry.

Importing this package registers every built-in predicate.
"""

from git_tutorial.predicates import composition, core, extended  # noqa: F401
from git_tutorial.predicates.base import (
    REGISTRY,
    ArgsSpec,
    AssertionResult,
    EvalContext,
    Predicate,
    evaluate,
    get,
    register,
)

__all__ = [
    "REGISTRY",
    "ArgsSpec",
    "AssertionResult",
    "EvalContext",
    "Predicate",
    "evaluate",
    "get",
    "register",
]
