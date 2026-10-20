#!/usr/bin/env bash
#
# git-tutorial launcher.
#
# Sets everything up, starts the watcher (which also serves the browser
# view), opens your browser, and leaves you in a shell inside your
# workspace. Safe to run again at any time; it picks up where you left off.
#
#   ./play.sh              start or resume
#   ./play.sh --watch      run only the watcher, in this terminal
#   ./play.sh --restart    throw your workspace away and begin again
#   ./play.sh --where DIR  put the workspace somewhere else
#   ./play.sh --help
#
# By default the workspace is created beside this repository.

set -euo pipefail

if [ -t 1 ] && [ -z "${NO_COLOR:-}" ]; then
  BOLD=$'\033[1m'; DIM=$'\033[2m'; RED=$'\033[31m'; GREEN=$'\033[32m'
  YELLOW=$'\033[33m'; RESET=$'\033[0m'
else
  BOLD=''; DIM=''; RED=''; GREEN=''; YELLOW=''; RESET=''
fi

say()  { printf '%s\n' "$*"; }
step() { printf '  %s%s%s\n' "$DIM" "$*" "$RESET"; }
ok()   { printf '  %s+%s %s\n' "$GREEN" "$RESET" "$*"; }
warn() { printf '  %s!%s %s\n' "$YELLOW" "$RESET" "$*"; }

die() {
  printf '\n  %sCannot start.%s %s\n\n' "$RED$BOLD" "$RESET" "$1" >&2
  shift || true
  for line in "$@"; do printf '  %s\n' "$line" >&2; done
  printf '\n' >&2
  exit 1
}

# ------------------------------------------------------------------- options

WHERE="${GIT_TUTORIAL_PLAY_DIR:-}"
RESTART=0
WATCH=0

while [ $# -gt 0 ]; do
  case "$1" in
    --watch)   WATCH=1; shift ;;
    --restart) RESTART=1; shift ;;
    --where)   WHERE="${2:?--where needs a directory}"; shift 2 ;;
    -h|--help) sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) die "I do not understand the option '$1'." "Try: ./play.sh --help" ;;
  esac
done

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ENGINE_DIR="$ROOT/engine"
LEVELS_DIR="${GITTUTORIAL_LEVELS:-$ROOT/content/src/git_tutorial_content}"
WHERE="${WHERE:-$ROOT}"

[ -f "$ENGINE_DIR/pyproject.toml" ] || die "I cannot find the engine in $ENGINE_DIR"
[ -f "$LEVELS_DIR/manifest.yaml" ] || die "I cannot find the levels in $LEVELS_DIR"

say ""
say "  ${BOLD}git-tutorial${RESET}  ${DIM}Tallowmere Distribution${RESET}"
say ""

# ------------------------------------------------------------- prerequisites

command -v git >/dev/null 2>&1 || die \
  "git is not installed, and this tutorial is about git." \
  "" \
  "macOS:   xcode-select --install" \
  "Ubuntu:  sudo apt install git" \
  "Windows: https://git-scm.com/download/win"

PYTHON=""
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 &&
     "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null
  then PYTHON="$candidate"; break; fi
done
[ -n "$PYTHON" ] || die \
  "I need Python 3.11 or newer and could not find it." \
  "" \
  "macOS:   brew install python" \
  "Ubuntu:  sudo apt install python3 python3-venv" \
  "Windows: https://www.python.org/downloads/"

ok "git $(git --version | sed 's/git version //')"
ok "python $("$PYTHON" -c 'import platform; print(platform.python_version())')"

if ! git config --get user.email >/dev/null 2>&1; then
  warn "git does not know who you are yet. Worth setting up:"
  say  "      git config --global user.name  \"Your Name\""
  say  "      git config --global user.email \"you@example.com\""
  say  "    The tutorial uses a placeholder until you do."
fi

# ------------------------------------------------------------------ the tools

VENV="$ROOT/.venv"
STAMP="$VENV/.play-stamp"
WANT="$("$PYTHON" -c 'import platform; print(platform.python_version())')|wt"
if [ ! -x "$VENV/bin/wt" ] || [ "$(cat "$STAMP" 2>/dev/null || true)" != "$WANT" ]; then
  step "Setting up (this happens once, and takes a moment)..."
  "$PYTHON" -m venv "$VENV" >/dev/null 2>&1 || die \
    "I could not create a Python environment in $VENV" \
    "On Ubuntu this usually means: sudo apt install python3-venv"
  "$VENV/bin/pip" install --quiet --upgrade pip >/dev/null 2>&1 || true
  "$VENV/bin/pip" install --quiet -e "$ENGINE_DIR" || die "Installing the engine failed."
  printf '%s' "$WANT" > "$STAMP"
fi
ok "tutorial installed"

export GITTUTORIAL_LEVELS="$LEVELS_DIR"
export PATH="$VENV/bin:$PATH"
# Tells `wt start` not to say "cd there": this script takes you there.
export GIT_TUTORIAL_ACTIVE=1
WORKSPACE="$WHERE/tallowmere-ops"

# ------------------------------------------------------------- the workspace

if [ "$RESTART" = 1 ] && [ -d "$WORKSPACE" ]; then
  printf '\n  This deletes %s and your progress in it. Type yes to continue: ' "$WORKSPACE"
  read -r answer
  [ "$answer" = "yes" ] || { say "  Left alone."; exit 0; }
  (cd "$WHERE" && wt start --reclone --fresh >/dev/null) || die "Rebuilding the workspace failed."
  ok "workspace rebuilt"
elif [ ! -d "$WORKSPACE/.git" ]; then
  step "Making your workspace..."
  mkdir -p "$WHERE"
  (cd "$WHERE" && wt start) || die "Setting up the workspace failed."
fi

if [ "$WATCH" = 1 ]; then
  cd "$WORKSPACE"
  exec wt
fi

# The watcher runs in the background for as long as the shell below does.
LOG="${GITTUTORIAL_HOME:-$HOME/.gittutorial}/wt.log"
mkdir -p "$(dirname -- "$LOG")"
(cd "$WORKSPACE" && PYTHONUNBUFFERED=1 exec wt) >"$LOG" 2>&1 &
WATCHER=$!
trap 'kill "$WATCHER" 2>/dev/null || true' EXIT

for _ in $(seq 1 30); do
  grep -q "open " "$LOG" 2>/dev/null && break
  sleep 0.3
done
URL="$(sed -n 's/.*open *//p' "$LOG" | head -1)"

say ""
say "  ${BOLD}Your workspace:${RESET} $WORKSPACE"
say "  ${BOLD}The warehouse:${RESET}  ${URL:-see $LOG}  (your browser should open on its own)"
say ""
say "  You are now in your workspace. Type git commands here and watch the"
say "  browser. Type ${BOLD}exit${RESET} when you are done for the day; progress is saved."
say ""

cd "$WORKSPACE"
"${SHELL:-bash}" -i || true
