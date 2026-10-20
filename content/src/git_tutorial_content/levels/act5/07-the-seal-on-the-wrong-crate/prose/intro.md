Marta asked you to seal the week ending 21 March: Theo's commit "Log
the week's dispatches". You pulled first, like a good trainee, and
typed `git tag dispatch-21-march`.

No hash. So the tag went on `HEAD`, and after the pull `HEAD` was
Ines's April price change, two commits newer. Marta noticed before
you pushed it.

A *tag* never moves on its own; that is its whole point. To move one,
delete it and make it again:

    git tag -d dispatch-21-march          delete the tag (your copy only)
    git tag dispatch-21-march <hash>      make it on the right commit

This is easy because the wrong tag never left your repository. Once a
tag has been pushed, other people may have fetched it, and changing it
means asking all of them to delete their copy. So check where a tag is
before you push it.

  try:  git log --oneline --decorate -n 4
        git ls-remote --tags origin

Move the tag, then send it up.
