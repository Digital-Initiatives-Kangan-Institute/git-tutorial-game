Three stale names gone, one live branch kept. `git branch -r` now says
what Head Office actually has.

A stale `origin/*` name does no harm on its own. The harm comes later,
when somebody sees `origin/pallet-audit`, assumes it is live, and
starts work on top of it. On a busy team, `git fetch --prune` is the
fetch worth typing by default.

Next job: Marta has a recount that needs booking and sealing.
