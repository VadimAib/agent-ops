# Working in this repository

This repository publishes the global rules and skills. The rules are in
`rules/AGENTS.md` and are installed to `~/.config/opencode/AGENTS.md`; skills are in
`skills/`. Only this file is read automatically when a session runs here.

- Edit `rules/AGENTS.md` or a skill in this repository, then copy it to the installed
  path and prove equality by hash. Never edit the installed copy: two copies of the same
  rules drift silently.
- Published surface is rules and skills only: no scripts, no measurement dumps, no
  third-party files, no project names, no personal paths.
- No counts or amounts in `README.md`, in the repository description or in a
  `description:` line - nobody updates those, and "ten rules" becomes a lie on the day a
  fourth skill appears. A dated measurement is fine; a standing promise is not.
- If `.agent-notes.md` exists in this directory, read it before changing anything: it
  holds this machine's measurements and traps and is never published.
