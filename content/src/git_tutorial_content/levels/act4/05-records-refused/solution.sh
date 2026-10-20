#!/usr/bin/env bash
set -euo pipefail

#: One commit of yours, finished and ready to send up.
git log --oneline -n 1

#: Which git refuses to send, and explains why.
git push || true

#: It is protecting Ines's commit. Take hers first.
git pull --no-edit

#: Both lines of work, joined by a merge.
git log --oneline --graph --all

#: Now the push has somewhere to go.
git push
git status
