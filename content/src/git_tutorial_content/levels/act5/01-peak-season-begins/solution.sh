#!/usr/bin/env bash
set -euo pipefail

#: Monday morning. Take Head Office's updates before anything else.
git status
git pull

#: Theo's Sunday hours are now on main. Branch from here.
git log --oneline -n 2
git switch -c peak-rota

#: The rota page itself.
mkdir -p rota
cat > rota/peak.md <<'MD'
# Peak season rota

    Mon - Fri   early 06:00 - 14:00   late 12:00 - 20:00
    Saturday    07:00 - 11:00
    Sunday      08:00 - 12:00

Theo leads the early shift. The trainee shadows the late shift in week one.
MD

#: Book it in on the branch.
git add rota/peak.md
git commit -m "Add the peak season rota"

#: Send the branch up, and remember where it belongs.
git push -u origin peak-rota
git status
