`git status` is quiet, the opening checks are committed, and the
scanner's exports are exactly where they were.

That last part matters. Ignoring a file does not delete it, does not
hide it from you, and does not stop the scanner writing it. It tells
git to stop asking you about it.

In a software job this will be `node_modules`, or a `.env` full of
passwords, and you will be the person who does not commit it. Next
job, a sheet goes on the bench by mistake.
