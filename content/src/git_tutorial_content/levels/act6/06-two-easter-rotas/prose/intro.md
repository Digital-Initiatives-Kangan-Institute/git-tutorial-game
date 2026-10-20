Easter is the first weekend of April, and Marta asked for a rota by
Thursday. You wrote `rota/easter.md` after lunch, covering Easter
Monday and the Tuesday, and committed it.

What you did not know is that she asked Theo too. He wrote a file with
the same name, covering Good Friday and the Saturday, and sent it up
an hour ago.

That is an *add/add* conflict. Neither file existed before, so there is
no older version to compare against: git puts the two new files side by
side, fences off the lines where they differ, and `git status` lists
the file as "both added". The browser calls it "added by both".

Before you edit, find out whose the other draft is. `git log --merge`
lists the commits on both sides that touched the conflicted file:
yours, and one other.

Nobody is wrong this time. Marta wants one rota with all four days. So
this is a hand-merge: keep the lines from both sides, put them in date
order under the one heading, and take the markers out.

  try:  git pull
        git status
        git log --merge

Answer the question, combine the rotas, and push.
