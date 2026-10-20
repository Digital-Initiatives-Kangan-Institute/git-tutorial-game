Incident report from Marta: three things are wrong this morning, and
they are wrong in three different ways.

*Aisle B.* You started counting bin B-16, got called to the gate
mid-sentence, and `stock/aisle-b.md` now ends with "if you count the".
Never committed. Never staged. It is still on the loading floor.

*Last night's commit.* You were stopping for the day with a returns
section half-written in `docs/receiving.md`, so you committed it as
`WIP: start on the returns section` to have somewhere to come back to.
In the cold light of morning the section should not exist. The commit
is yours and has never left this machine.

*Thursday's commit.* `Update the pallet wrap price`, two commits further
down, with the wrong price in it. Head Office already has it.

You have a tool for each of these, and you have used all three. This
act has not asked you to choose between them before.

The question that chooses for you is always the same:

    how far has this got?

  still in your working tree   `restore` it; no history to change

  committed, yours alone       `reset`; move the label, nobody else
                               has a copy to disagree with

  committed and shared         `revert`; add a commit that undoes it,
                               change nothing that exists

The grading is on the choices: a reverted WIP commit would leave two
commits where nobody wanted any, and a reset price commit would rewrite
history Head Office is holding.

  try:  git status
        git log --oneline

Aisle B as committed, the WIP commit gone, the price commit undone not erased.
