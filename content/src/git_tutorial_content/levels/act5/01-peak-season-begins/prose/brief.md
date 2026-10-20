Pull, branch, commit, push. In that order.

  git pull                        Theo's commit arrives on main
  git switch -c peak-rota         a branch from the updated main
  (write `rota/peak.md`, starting with `# Peak season rota`)
  git add rota/peak.md
  git commit -m "Add the peak season rota"
  git push -u origin peak-rota    send it up and set the upstream
  git status

Branching before pulling builds your rota on last week's records.
