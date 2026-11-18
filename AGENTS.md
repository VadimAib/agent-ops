<!-- agent-ops: installed by sync.ps1. Edits here will be overwritten; change the repo. -->
# Global rules (all projects)

A project `AGENTS.md` overrides these rules where they disagree.

1. **No invented facts.** A claim about product behaviour, a library or a number comes only from a file, a command or a link. Without evidence say "no data", not a guess.
2. **Measure, don't guess.** "Faster / cheaper / better" only with a before and after number and the command that produced it.
3. **Money is in the provider's currency.** A UI may label an amount in another one. Estimate = tokens × provider price; check the `currency` field, and never read `$` in a UI as a currency.
4. **Volume sets the step price, not the token rate.** Almost all tokens of a step are the prefix read again, paid on every step. So: read a file once and in slices (`offset`/`limit`, `grep` instead of the whole file), give heavy reading to a subagent (its session is cheaper than the root one), split long tasks, keep answers short.
5. **Never install plugins that rewrite context.** A changed prefix drops the cache and the next request goes as fresh input — dearer than the saving.
6. **Console follows OS rules.** Windows + pwsh: encodings, the silent pipeline, a strict command scanner rejecting a command — see the `windows-console` skill instead of retrying blindly.
7. **Code Mode boundaries.** `execute` is for the browser and sessions only. Files, commands and edits go through regular tools (`read`, `edit`, `write`, `shell`).
8. **Secrets** never reach git, a browser or an answer. Read them from files only; report that they exist, never their value.

Details: skills `windows-console` and `harness-cost`.
