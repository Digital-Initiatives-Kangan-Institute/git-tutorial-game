Corrected before anyone saw it. `dispatch-21-march` is on the week's
dispatch log here and at Head Office, and Ines's April commits are
untouched.

The lesson is in the order: look, then push. `git log --decorate`
before `git push origin <tag>` costs a second. A wrong tag that has
already been fetched by the whole team costs a message to all of them.

Next job: Theo's branch has vanished from Head Office, and your
repository still thinks it is there.
