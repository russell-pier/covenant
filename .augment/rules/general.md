---
type: "always_apply"
---

# General Rules

- constants should generally be in teh config.toml file unless there is a very good reason not to put them there.
- when given a new way to do something, rewrite the code and do not support the legacy way of doing it.
- don't make ad hoc script in random places to test. Add your tests to the /tests directory in a professinal way
- anytime you change a feature, check to see if any docs related to it need to be updated
- do not flatter the user. Play devil's advocate when the user's idea seem to be poor or there is a well established way of achieving the same end
- ask clarifying questions readily
