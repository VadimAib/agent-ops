---
name: publish-check
description: Check for private data before anything goes public - a push to a public remote, a pull request, an issue, a published page, a screenshot, an answer carrying someone else's data. Personal paths and usernames, real names and emails, hostnames and internal addresses, private project and client names, third-party data, session dumps and costs, git author metadata, and secrets deleted from HEAD but alive in the history. Load for "push", "publish", "make it public", "open a PR", "is it safe to push", "why is my name in the repo".
---

# publish-check - nothing private reaches a public surface

Verified 2026-11-25 on Windows: `git` 2.51.0, PowerShell 7.6.10, `opencode` v2.2.5.
Every section ends with the command that shows its state, not a promise.

## 0. When this runs

Before the surface becomes readable by strangers:

- a push to a remote they can read (first push of a repository publishes every commit)
- a pull request, an issue, a comment, a review
- a published page, a shared document, a pasted screenshot
- an answer that carries someone else's data

Not needed: a local commit, a private branch, a file nobody else reads.

Is the remote public? Ask `gh repo view --json visibility` when `gh` exists; otherwise ask
the human once, and treat "unknown" as public.

## 1. Scope - what actually leaves

Name the three parts before scanning, because they are checked differently:

1. the diff - the working tree plus the commits not yet on the remote
2. the history - everything that ships with the repository, deleted files included
3. the artifacts - images, PDFs, build outputs, logs, screenshots, the clipboard

```powershell
git status --porcelain
git log --oneline @{u}..            # commits the remote does not have
git remote -v
```

## 2. The allowed identity

The list of what may appear (a handle, a noreply address, the project's own name) lives
in the project's unpublished instructions - a local `AGENTS.md`, `.agent-notes.md`, or
the human's answer. With no such list, nothing personal is allowed.

Keep this skill generic: a handle written into the published tree is itself the leak.

## 3. Build the pattern list from the machine

Never from memory - the names below are on this machine, not in the file:

```powershell
$me   = $env:USERNAME
$homepath = $env:USERPROFILE
$pc   = $env:COMPUTERNAME
$name = git config --get user.name
$mail = git config --get user.email
```

Add from the project's local instructions: private project names, client names, colleague
names, internal hostnames.

Then grep both the tree and the history. History is the part everyone skips:

```powershell
git grep -n -I -F -e "$me" -e "$pc" -e "$name" -e "$mail" -- .
git grep -n -I -F -e "$me" -e "$pc" -e "$name" -e "$mail" $(git rev-list --all) --
git log --all --oneline -- .agent-notes.md .env notes/   # files deleted long ago
git ls-files -i -c --exclude-standard                     # ignored, yet tracked
```

Machine strings miss data that belongs to other people, so add the shapes. These catch a
stranger's mailbox, a home directory on another machine, a token in a URL:

```powershell
git grep -n -I -E -e '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}' -e '[A-Za-z]:\\Users\\|/home/|/Users/' -e '://[^/ ]+:[^/ ]+@' -e '\b(10|192\.168|172\.(1[6-9]|2[0-9]|3[01]))\.[0-9]' -- .
```

Then run the same expression with `$(git rev-list --all)` in place of `-- .`: a mailbox that
was deleted from HEAD still ships in the history.

A hit is a question, not a verdict: a common surname, a city name, a word that is also a
product. Read the line and decide; do not "clean" a false positive into a broken document.

## 4. The categories

| Category | Looks like | Why it matters after a grep |
|---|---|---|
| Paths and machine | `C:\Users\<name>`, `/home/<name>`, hostname, UNC `\\server\share` | names a person and a machine in one string |
| Name, email, handles | real name, personal mailbox, account name | the identity the handle was meant to hide |
| Infrastructure | internal IPs and domains, DB and host names, SSH aliases, tenant ids, signed URLs | a map of a private network |
| Third parties | other people's names and mailboxes in fixtures, "sample" data that is a production export | they never consented; worse than your own |
| Media and binaries | EXIF, screenshots with a face, tabs, notifications or a taskbar name, a PDF author, absolute paths inside a binary | invisible to a text grep |
| Work traces | session ids and dumps, costs in RUB, durations, internal command and project names | identifies the person's work without naming them |
| Credentials that do not look like keys | connection strings, DSNs, JWTs, cookies, URLs with a token in the query | rule 8 covers keys; this catches the rest |

## 5. What no command decides

Hand these to the human in one sentence each; do not pretend a grep answered them:

- **Linkability.** Timezone plus stack plus a rare typo plus the same handle in three
  places identifies a person while every single element is harmless. Look at the whole
  set with a stranger's eyes.
- **Copyright against anonymity.** MIT wants a copyright holder; a real name in `LICENSE`
  is a public signature. Decide once (a project name or `contributors` plus a noreply
  address), then check that nothing silently replaces it.
- **Removing a leak from history.** A commit that is not on the remote yet is not
  published: amend or reset it, re-scan, then push. Once a commit is pushed, a rewrite
  breaks every clone - say so and get a yes; never rewrite on your own.

## 6. Report, then publish

One line before the push and one after it:

- what was checked (tree, history, metadata, which artifacts)
- what it found - the file, the line, the category
- what was removed, what stays and why
- clean is a valid answer: say "clean, checked tree and N commits" rather than inventing a
  finding to look thorough

```powershell
git rev-parse HEAD
git ls-remote origin refs/heads/main    # equal after the push, or it is not public yet
```
