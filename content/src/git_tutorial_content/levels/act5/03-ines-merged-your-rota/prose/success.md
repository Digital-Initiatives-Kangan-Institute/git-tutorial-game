Tidy. The rota is in `main`, and `peak-rota` is gone from your
repository and from Head Office.

Two commands, because there were two branches. `git branch -d` only
ever touches your repository; Head Office keeps its copy until you ask
with `git push origin --delete`. And you pulled before deleting, so you
saw the rota inside `main` before you let its name go.

Next job: Ines has been clearing branches at Head Office too, and your
repository has not noticed.
