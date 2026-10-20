Pull, find whose rota is the other one, combine both, push.

  git pull                 stops: both added rota/easter.md
  git status               "both added"
  git log --merge          the commits on both sides, with authors
  git add rota/easter.md   settled
  git commit --no-edit
  git push

The finished file: the heading once, then all four days in date order.

    # Easter rota

    - Good Friday 3 April: Theo and Ines
    - Saturday 4 April: Theo
    - Easter Monday 6 April: Marta and the trainee
    - Tuesday 7 April: the trainee

`git restore --ours` or `--theirs` would each throw away two days.
