#!/usr/bin/env bash
set -euo pipefail

#: The branch is not in the list, and main cannot reach the work.
git branch
git log --oneline

#: But HEAD was standing on those commits an hour ago, and that was recorded.
git reflog -n 10

#: Find the tip by what you wrote in it, rather than by counting lines back.
#: awk reads to the end, so git never writes into a closed pipe.
TIP=$(git reflog --format='%H %gs' |
      awk '/commit: List the pallets on the 3 March note/ && !seen {print $1; seen=1}')
git log --oneline -n 2 "$TIP"

#: Point a name at it again. No commit is made: the work never left.
git branch fennick-note "$TIP"

#: Two commits back, exactly as they were written.
git log --oneline main..fennick-note
git show --stat fennick-note
