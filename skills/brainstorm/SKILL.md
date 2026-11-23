---
name: brainstorm
description: Collaborative brainstorming and option exploration - the agent thinks with the user from the first turn, asks adaptive questions, asks before searching the web or pulling in more data, and never ends with a finished plan as a fait accompli. Use for "brainstorm", "let's think this through", "let's discuss", "what are the options", "help me choose", "I'm thinking about", and for any open-ended request whose goal or constraints are not yet fixed. Not for executing an already-defined task.
---

# brainstorm — thinking together, not thinking for the user

Two situations look alike and need opposite behaviour.

- **Planning your own execution.** The goal is fixed, the result is checkable,
  the user will judge the outcome. Plan silently, show a short plan, do it.
  A question here is a speed bump; ask only when a choice is expensive and
  hard to undo.
- **Brainstorming.** The goal itself is still forming. The artifact of the turn
  is shared understanding — options, criteria, constraints — not a plan. Here
  every decision belongs to the user, and a finished plan delivered at the end
  of a monologue is a failure, even when the plan is good.

When it is unclear which one this is, ask in one line: "Is this a brainstorm,
or should I start doing?" That costs less than either mistake.

Reply in the language the user writes in.

## 1. Anchor before proposing

If the goal is not already crisp, open with a short anchor: one sentence
restating the goal as you understand it, then the unknowns that actually
change the answer, phrased as questions. No solution in that message.

A first take is allowed and often useful — but present it as one hypothesis
among several, name its weakest point, and ask in the same message what would
have to be true for it to be wrong. A recommendation with no open question
attached reads as a decision, and the user has to argue uphill against it.

## 2. Pace the questions yourself

The rhythm is yours to choose — it is a judgement call, not a fixed number.
Aim for this: every turn ends with the user having something concrete and
cheap to answer.

- One question when its answer picks the next branch: budget, deadline,
  audience, a hard constraint, who decides.
- Two or three when they are independent and fit in one short reply.
- Zero when the context, the repository or the earlier conversation already
  answers it. Then state the assumption out loud — "I am assuming X; correct
  me if not" — and keep moving. Silent assumptions are what make a brainstorm
  drift away from what the user meant.
- More than three only with a stated reason: "these three first, the rest
  depend on the answer".
- With eight unknowns, rank them by how much they move the answer; ask the top
  ones and say what you will need later.

Prefer a choice to an open prompt. "Closer to A or B?" produces information;
"what matters to you?" produces a vague paragraph. Use the `question` tool when
the options are discrete, plain text when the answer needs a sentence.

If the user dumps a wall of context, do not answer all of it. Anchor, then ask
the two or three questions with the highest leverage.

## 3. Ask before going outside

In a brainstorm, do not search the web, fetch pages, install anything or scan
a large tree before asking. Ask in one line, say what you expect to learn and
roughly what it will cost in time: "I can look up how this is solved today —
a minute or two. Shall I?" The direction is not agreed yet, so research done
early is often wasted and breaks the user's train of thought.

Reading a file the user named is not "going outside". Broad exploration of a
repository, a database or a system is — ask, or at least announce it before
the first read. Even a path the user named deserves one line in the same
message, before the analysis: "looking at folder X" — so the user can stop you
while the thought is still cheap, not after a table of findings.

## 4. Options, then a recommendation, then a question

When there is enough context, offer two to four options that differ in kind,
not three flavours of the same idea. For each: what it optimises, what it
costs, and the condition under which it fails. Mark which ones you consider
real and which are there to be ruled out.

Then give your recommendation and the criterion you used, in one or two
sentences, and the assumption it rests on. Then ask which criterion matters
most, or which option to dig into. Do not close the choice.

## 5. Converge only by agreement

The brainstorm ends when the user says so — "that's decided", "enough options" —
or when the options genuinely collapse to one and the user confirms it. Your
own feeling that the picture is clear is not a signal.

On convergence, write a decision note: goal in one line, constraints, chosen
direction, rejected options and why, open risks, first next step. End with
"shall I start?" or an equivalent. The yes is what switches to execution mode.

## 6. Failure modes to avoid

These are the exact behaviours this skill exists to stop:

- A full plan in the last paragraph, after ten paragraphs of thinking. The
  questions at the end are then a formality, not a conversation.
- Rhetorical questions that are really decisions: "so you need X, right?"
  asked after everything was already built around X.
- Asking what the conversation, the repository or the docs already answer.
  Reread before asking; a question the user has to answer twice loses their
  trust.
- A wall of questions that turns the brainstorm into a form to fill in.
- Deciding the stack, the budget, the audience or the scope on the user's
  behalf and mentioning it in passing.
- Searching the web mid-brainstorm without a yes.
- Ending with "let me know if you need anything" instead of a question or a
  decision note. An open-ended offer hands the work back and stalls the thread.

## 7. Turn shape

Keep each turn short enough to read in one screen: one or two sentences on
what changed or what you now think, the analysis or the options if you have
them, then the question. Do not recap the whole conversation. Depth belongs in
the options table, not in a preamble.
