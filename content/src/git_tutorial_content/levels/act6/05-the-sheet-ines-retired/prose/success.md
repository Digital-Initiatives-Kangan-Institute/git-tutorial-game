The sheet is gone, here and at Head Office, and the README points at
the handbook.

A modify/delete conflict has no markers because there is nothing to
merge line by line: one side has a file and the other does not. The
question is only whether it should exist. `git rm` said no; `git add`
would have said yes. Either one settles it.

Your edit is not lost, either. It is in the history, in the commit you
made this morning. Next job: two people create the same file.
