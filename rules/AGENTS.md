# Global rules (all projects)

A project `AGENTS.md` overrides these rules where they disagree.

1. **No invented facts.** A claim about behaviour, an API or a number comes from a file, a command or a link. Without evidence say "no data" - a guess is worse than a gap.
2. **Measure, don't guess.** "Faster", "cheaper", "better" only with a before and after number and the command that produced it.
3. **Numbers carry units.** Tokens, milliseconds, megabytes, currency: name it. Take an amount from the source's own price list or report, never from a label on a screen.
4. **Volume sets the bill.** In a long session most tokens are the same context sent again. Read a file once and in slices; split long tasks; keep answers short. Independent calls belong in one step: two reads, or a read and a grep, are billed once instead of twice. A subagent costs tens of steps of its own - hand it only reading too bulky to keep in this context, never a one-file check.
5. **Do not rewrite what was already sent.** Tools that compress or edit the conversation drop the prompt cache: the next request is billed in full and costs more than it saves.
6. **Read the error before retrying.** Encoding, quoting and pipelines differ between shells and systems; a rejected command is a verdict, not bad luck.
7. **One tool per job.** Edit files with the editor, run commands in the shell, work on pages in the browser. A sandbox stand-in drifts from the real workspace.
8. **Secrets never reach output.** No key or password in an answer, a commit or a page: read it from a file and report that it exists.
9. **A bad call costs a step.** Pass `path` and copy the exact anchor from the last `read`/`grep` of that file instead of retyping it; an `edit` whose `oldString` equals `newString` is a no-op. Do not re-read a file only to edit it: one extra step per edit costs more than the failures it prevents. A call whose answer is already in the context is a step paid for nothing.
10. **Review by risk, and ask before spending.** A milestone gets the full fleet; shared surfaces (API contract, permissions, storage, settings schema) three to five by risk; ordinary code two or three; a cosmetic change one; an unchanged diff is never re-reviewed. Close a turn that changed code with one question naming the surface, the set and its price, written as plain text at the end of the reply - a question tool is one more paid step, and in a non-interactive run it waits forever; docs only - no question. Path map, counts and prices: skill `review-team`.
11. **A new goal is a new session.** Split on the goal boundary, never to shorten a session: the price of a step is flat, and a restart re-sends the context as fresh input. Mid-goal, split only when the work circles back to an approach that already failed. Say it in one sentence at the end of the reply, in the same wording each time, with a short handoff: done, open, decided.

Details: skills `windows-console`, `harness-cost`, `review-team`.
