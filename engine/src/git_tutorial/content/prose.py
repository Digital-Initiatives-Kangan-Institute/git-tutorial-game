"""Level prose: a small markdown dialect, parsed for the browser."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from git_tutorial.errors import LevelAuthoringError
from git_tutorial.git.snapshot import RepoSnapshot
from git_tutorial.levels.model import Level

SHORT_LEN = 7


@dataclass(frozen=True, slots=True)
class Paragraph:
    text: str


@dataclass(frozen=True, slots=True)
class Heading:
    text: str


@dataclass(frozen=True, slots=True)
class Bullet:
    text: str


@dataclass(frozen=True, slots=True)
class Verbatim:
    lines: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TryBlock:
    commands: tuple[str, ...]


Block = Paragraph | Heading | Bullet | Verbatim | TryBlock


@dataclass(frozen=True, slots=True)
class ProseDocument:
    blocks: tuple[Block, ...]

    @property
    def try_blocks(self) -> tuple[TryBlock, ...]:
        return tuple(b for b in self.blocks if isinstance(b, TryBlock))


@dataclass(frozen=True)
class SubstitutionContext:
    shas: Mapping[str, str] = field(default_factory=dict)
    snapshot: RepoSnapshot | None = None
    level: Level | None = None
    resolver: object | None = None  # an EvalContext, when live resolution is wanted


_TOKEN = re.compile(r"\{\{\s*(sha|short|ref|branch|level)\s*(?::\s*([^}]*?))?\s*\}\}")
_ESCAPE = "\0GQBRACE\0"


def substitute(text: str, ctx: SubstitutionContext, *, strict: bool = True) -> str:
    text = text.replace("{{{{", _ESCAPE)

    def replace(match: re.Match[str]) -> str:
        kind, arg = match.group(1), (match.group(2) or "").strip()
        if kind in ("sha", "short"):
            sha = ctx.shas.get(arg)
            if sha is None:
                if strict:
                    raise LevelAuthoringError(
                        f"{{{{{kind}:{arg}}}}}: no {arg!r} in the pack's sha_manifest.json"
                    )
                return match.group(0)
            return sha[:SHORT_LEN] if kind == "short" else sha
        if kind == "ref":
            return _resolve_ref(arg, ctx)
        if kind == "branch":
            if ctx.snapshot is None:
                return "(unknown)"
            return ctx.snapshot.head_ref or "(detached)"
        return _level_field(arg, ctx, strict=strict)

    return _TOKEN.sub(replace, text).replace(_ESCAPE, "{{")


def _resolve_ref(name: str, ctx: SubstitutionContext) -> str:
    """Never raises: prose must still print in a repo the student has broken."""
    if ctx.resolver is None:
        return name
    try:
        from git_tutorial.predicates.resolve import resolve as resolve_ref

        return resolve_ref(ctx.resolver, name)[:SHORT_LEN]  # type: ignore[arg-type]
    except Exception:
        return name


def _level_field(arg: str, ctx: SubstitutionContext, *, strict: bool) -> str:
    if ctx.level is None:
        return "(unknown)"
    fields = {
        "title": ctx.level.title,
        "id": ctx.level.id,
        "act": str(ctx.level.act),
        "number": str(ctx.level.level),
        "label": ctx.level.label,
    }
    if arg not in fields:
        if strict:
            raise LevelAuthoringError(
                f"{{{{level:{arg}}}}}: unknown field. Known: {', '.join(sorted(fields))}"
            )
        return f"{{{{level:{arg}}}}}"
    return fields[arg]


_TRY = re.compile(r"^(?P<indent>[ \t]*)try:[ \t]*(?P<first>.*)$")


def parse_prose(text: str) -> ProseDocument:
    blocks: list[Block] = []
    lines = text.replace("\r\n", "\n").split("\n")
    index = 0
    paragraph: list[str] = []

    def flush() -> None:
        if paragraph:
            blocks.append(Paragraph(" ".join(s.strip() for s in paragraph).strip()))
            paragraph.clear()

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if not stripped:
            flush()
            index += 1
            continue

        match = _TRY.match(line)
        if match:
            flush()
            index = _consume_try(lines, index, match, blocks)
            continue

        if stripped.startswith("```"):
            flush()
            index = _consume_fence(lines, index, blocks)
            continue

        if stripped.startswith("#"):
            flush()
            blocks.append(Heading(stripped.lstrip("#").strip()))
            index += 1
            continue

        if stripped.startswith(("- ", "* ")):
            flush()
            blocks.append(Bullet(stripped[2:].strip()))
            index += 1
            continue

        # An indented run is preformatted: numbered questions, command
        # listings and answer stubs must keep their own lines rather than
        # being reflowed into a paragraph.
        if not paragraph and line[:1] in (" ", "\t"):
            flush()
            index = _consume_indented(lines, index, blocks)
            continue

        paragraph.append(line)
        index += 1

    flush()
    return ProseDocument(tuple(blocks))


def _consume_try(
    lines: list[str], index: int, match: re.Match[str], blocks: list[Block]
) -> int:
    """A try: line, then lines indented deeper, closed by a blank line.

    Parsing this structurally rather than regexing the raw text is what makes
    "every arrival beat ends with commands to try" a checkable property.
    """
    indent = len(match.group("indent").expandtabs(4))
    commands: list[str] = []
    if match.group("first").strip():
        commands.append(match.group("first").strip())

    index += 1
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            break
        depth = len(line.expandtabs(4)) - len(line.expandtabs(4).lstrip())
        if depth <= indent:
            break
        commands.append(line.strip())
        index += 1

    if not commands:
        raise LevelAuthoringError("a `try:` block must list at least one command")
    blocks.append(TryBlock(tuple(commands)))
    return index


def _consume_indented(lines: list[str], index: int, blocks: list[Block]) -> int:
    body: list[str] = []
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            break
        if line[:1] not in (" ", "\t"):
            break
        body.append(line.rstrip())
        index += 1
    # Strip the common indent; to_plain re-applies a uniform two spaces.
    depth = min((len(s) - len(s.lstrip()) for s in body if s.strip()), default=0)
    blocks.append(Verbatim(tuple(s[depth:] for s in body)))
    return index


def _consume_fence(lines: list[str], index: int, blocks: list[Block]) -> int:
    index += 1
    body: list[str] = []
    while index < len(lines) and not lines[index].strip().startswith("```"):
        body.append(lines[index])
        index += 1
    blocks.append(Verbatim(tuple(body)))
    return index + 1 if index < len(lines) else index


ProseKey = Literal["intro", "brief", "success"]


def load_prose(level: Level, key: ProseKey) -> str | None:
    rel: str | None = getattr(level.prose, key, None)
    if not rel:
        return None
    path = Path(level.directory) / rel
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def to_blocks(doc: ProseDocument) -> list[dict[str, Any]]:
    """The document as JSON for the browser.

    Inline markup (`code`, **strong**, *emphasis*) is left in the text: the
    page escapes it first and then marks it up, so prose can never inject
    HTML into the student's browser.
    """
    out: list[dict[str, Any]] = []
    for block in doc.blocks:
        if isinstance(block, Paragraph):
            out.append({"type": "p", "text": block.text})
        elif isinstance(block, Heading):
            out.append({"type": "h", "text": block.text})
        elif isinstance(block, Bullet):
            out.append({"type": "li", "text": block.text})
        elif isinstance(block, Verbatim):
            out.append({"type": "pre", "lines": list(block.lines)})
        else:
            out.append({"type": "try", "commands": list(block.commands)})
    return out


def blocks_for(level: Level, key: ProseKey, ctx: SubstitutionContext) -> list[dict[str, Any]]:
    """Load, substitute and parse one of a level's prose files. Never raises:
    a broken prose file must not take the student's page down."""
    text = load_prose(level, key)
    if text is None:
        return []
    try:
        return to_blocks(parse_prose(substitute(text, ctx, strict=False)))
    except LevelAuthoringError as exc:
        return [{"type": "p", "text": f"(this text could not be shown: {exc})"}]
