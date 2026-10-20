#!/usr/bin/env bash
set -euo pipefail

#: The note stops mid-sentence. Here is where it stops.
tail -2 dispatch/2025-03-03.md

#: Finish it. Any ending will do. You would type this in your editor;
#: a script has to append the line instead, which is what >> does.
printf 'marked FRAGILE: glazed pots.\n' >> dispatch/2025-03-03.md

#: Read what you wrote before recording it.
git diff

#: Two steps, as before.
git add dispatch/2025-03-03.md
git commit -m "Finish the 3 March dispatch note"
