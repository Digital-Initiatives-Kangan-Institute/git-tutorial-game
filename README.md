# git-tutorial

Learn git by running a warehouse.

You are the new trainee at **Tallowmere Distribution**. Its stock counts,
dispatch notes and supplier prices are kept in a git repository, and every
job you are given is a real git task in that repository. You type real git
commands in your own terminal. A browser window shows the job, checks your
work as you go, and draws the repository as a warehouse, so you can see what
each command moved.

## Playing

From a clone of this repository:

    ./play.sh

That checks the prerequisites (git 2.23+, Python 3.11+), installs the
tutorial into a private environment, makes your workspace
(`tallowmere-ops/`), starts the watcher, opens your browser, and leaves you
in a shell inside the workspace. Run it again any time to carry on.

You need two things on screen:

    your terminal   where you type git commands, in tallowmere-ops/
    your browser    the job, the job sheet, hints, and the warehouse

The browser updates on its own within a second of any change.

## How it fits together

    workspace (your terminal)        watcher (`wt`)                  browser
    ─────────────────────────        ──────────────                  ───────
    git add / commit / push ...  →   polls the repo, grades the  →   job card, job sheet,
                                     job, works out what moved,      hints, the animated
                                     serves the page and its state   warehouse

- **One process watches and serves.** `wt` grades the repository and runs
  the web server. One snapshot per change feeds both the job sheet and the
  picture, so they can never disagree. One thread owns all progress; the
  browser's buttons queue commands for it.
- **Real git, always.** Nothing is simulated. The tutorial reads your
  repository and never writes to it, except when a job sets itself up
  (which happens only when you press **Start the next job**, never on its
  own).
- **Head Office is a real remote.** `origin` is a bare repository on your
  own computer (`~/.gittutorial/head-office.git`). In Act 4 your colleague
  Ines pushes to it, and you fetch, pull and push for real.
- **The browser is local only.** The server listens on 127.0.0.1. It refuses
  requests that claim any other host, and every button press needs a
  per-run token, the page's own origin and a JSON body. That stops other
  websites reaching your repository through your browser.

## The story wraps the real terms

The warehouse is the picture: the working tree is the loading floor, the
staging area is the packing bench, a commit is a sealed crate, a branch is a
shelf line, HEAD is the forklift, and origin is Head Office. But every goal
on the job sheet, every question and every hint after the first names the
real git term and command. Students leave knowing git, not a metaphor.
`content/tests/test_content.py` enforces this.

## The course

| Act | Story | Teaches |
|---|---|---|
| 1 | First shift: booking in | status, log, add, commit, diff, restore, .gitignore |
| 2 | Parallel jobs | branch, switch, log --graph, stash, merge, conflicts |
| 3 | Incident reports | checkout, reflog, reset, revert |
| 4 | Head Office | clone, remote, fetch, push, pull, rejected pushes, force-with-lease |

42 jobs in all. Each introduces at most two new commands. Every drilled
command is practised three times, spaced out (`content/tests/test_curriculum.py`).

## Commands

| Command | What it does |
|---|---|
| `wt` | the watcher and browser view; run it in your workspace |
| `wt start` | make (or resume) your workspace |
| `wt answer ID VALUE` | answer a job-sheet question from the terminal |
| `wt check` | grade the current job once and print the job sheet |
| `wt next` | start the next job (the current one must be complete) |
| `wt reset` | put the workspace back to the start of the current job |
| `wt solve` | do the current job for you, explaining each step |
| `wt doctor` | check this machine can run the tutorial |

## The single-file build

    python3 tools/build_zipapp.py        # -> dist/wt.pyz

`wt.pyz` contains the engine, the levels, the browser page and a pure-Python
PyYAML. Copy it anywhere with Python 3.11 and git:

    python3 wt.pyz start
    cd tallowmere-ops && python3 ../wt.pyz

## Layout

    engine/      the `wt` package: git probing, grading, sessions, the watcher,
                 the web server and the browser page (src/git_tutorial/web/assets)
    content/     the level pack: manifest, 42 levels, glossary, and the practice
                 history (history/script.yaml -> depot.bundle, byte-reproducible)
    tools/       the zipapp builder
    play.sh      the launcher

## Running the tests

    python3 -m venv .venv && .venv/bin/pip install -e 'engine[dev]'
    cd engine  && ../.venv/bin/python -m pytest && ../.venv/bin/mypy --strict src && ../.venv/bin/ruff check src tests
    cd content && ../.venv/bin/python -m pytest

The content suite sets up every level, runs its `solution.sh`, and checks the
job sheet passes. It also checks that setup is idempotent, that no level is
solved before the student starts, and that the practice history rebuilds
byte for byte.

Everything here is invented: Tallowmere Distribution, its staff, Kestrelby
Packaging, Fennick Garden Centre. Phone numbers are in Ofcom's 01632 960xxx
range reserved for fiction.
