---
name: publish-check
description: Check what becomes readable by strangers before a push, a pull request, an issue, a published page, a screenshot or an answer carrying someone else's data - personal paths and usernames, names and emails, hostnames, private project and client names, third-party data, session dumps, git author metadata, secrets in the deleted history. Not for a local commit, a private branch or a push only you can read. Load for "push", "publish", "make it public", "open a PR", "is it safe to push", "why is my name in the repo".
---

# publish-check - nothing private reaches a public surface

Verified 2026-11-25 on Windows: `git` 2.51.0, PowerShell 7.6.10, `opencode` v2.2.5.

## 0. When this runs

Before the surface becomes readable by strangers: a push to a remote they can read (a first
push publishes every commit), a pull request, an issue, a comment, a published page, a pasted
screenshot, an answer carrying someone else's data. Not for a local commit, a private branch,
or a push only you can read.

Is the remote public? `gh repo view --json visibility`; otherwise ask once, and treat
"unknown" as public.

## 1. Scope - what actually leaves

1. the diff - the working tree plus the commits the remote does not have
2. the history - everything that ships with the push, deleted files included
3. the artifacts - images, PDFs, build outputs, logs, screenshots, the clipboard

```powershell
git status --porcelain
git log --oneline --not --remotes      # works with no upstream, also on the first push
git remote -v
```

## 2. The allowed identity

From the human in this session, or from a local notes file that is not part of the published
tree - an ignored `AGENTS.md` is fine. A file inside the repository cannot whitelist itself:
what it "allows" is still a question. With no list, nothing personal is allowed.

## 3. Patterns from the machine

Built here, never remembered:

```powershell
$me   = $env:USERNAME
$pc   = $env:COMPUTERNAME
$name = git config --get user.name
$mail = git config --get user.email
if (-not $me -or -not $name -or -not $mail) { "a pattern is empty: set it before grepping" }
```

An empty `-e ""` matches every line; unset values flood the output and bury the real hit.
Add from the local notes: private project names, client names, colleague names, internal hosts.

## 4. Tree and history, both

```powershell
git grep --untracked -n -I -F -e "$me" -e "$pc" -e "$name" -e "$mail" -- .
git rev-list --all | ForEach-Object { git grep -n -I -F -e "$me" -e "$pc" -e "$name" -e "$mail" $_ }
```

`--untracked` matters: plain `git grep` reads tracked files only, so a new file leaks while
the report says "tree checked". The loop matters: `$(git rev-list --all)` is one command line,
and Windows rejects it near 800 commits.

Shapes, because machine strings miss other people's data:

```powershell
git grep --untracked -n -I -E -e '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}' -e '[A-Za-z]:\\Users\\|/home/|/Users/' -e '://[^/ ]+:[^/ ]+@' -e '\b(10|192\.168|172\.(1[6-9]|2[0-9]|3[01]))\.[0-9]' -- .
```

Credentials that are not a private key, over the tree and then over `git rev-list --all`:

```powershell
git grep --untracked -n -I -E -e 'AKIA[0-9A-Z]{16}' -e 'gh[pousr]_[A-Za-z0-9]{20,}' -e 'sk-[A-Za-z0-9]{20,}' -e 'eyJ[A-Za-z0-9_-]{10,}\.' -e 'BEGIN [A-Z ]*PRIVATE KEY' -e '[?&](token|key|sig|X-Amz-Signature|access_token)=' -e '(password|passwd|pwd)\s*[:=]' -- .
```

Metadata - the leak no content grep sees:

```powershell
git log --all --format='%h %an <%ae>' | Sort-Object -Unique
```

A real name, a corporate address or a timezone in an unpushed commit is a finding. Amend it
while it is local (`git commit --amend --reset-author`); after a push it needs a yes.

Ignored and deleted:

```powershell
git ls-files -i -c --exclude-standard   # nothing printed = none
git log --all --diff-filter=D --name-only --format=''   # deleted, still in history
git show <rev>:<path>                   # read what it held
```

Beyond the patterns: third-party data in fixtures, session dumps and costs, a screenshot with
a face, a tab or a taskbar name, a PDF author, EXIF, absolute paths inside a binary.

## 5. What no command decides

- **Linkability.** Name the two details that together point at one employer, city or account,
  or say none - this is the anonymity check.
- **Removing a leak.** Unpushed commit: amend or reset, re-scan, push. Pushed commit: the
  rewrite breaks every clone, so get a yes. Third-party data: removing it is the owner's call.
- **Copyright against anonymity.** A real name in `LICENSE` is a public signature; decide once
  and check that nothing silently replaces it.

## 6. Report, then publish

- what was checked: tree with untracked, all N commits, metadata, which artifacts - or state
  "binaries and media not examined"
- the hit: file, line, category
- a hit stops the push until the human answers; "clean, checked tree and N commits" is a valid
  answer - say it rather than inventing a finding

```powershell
git rev-parse HEAD
git ls-remote origin HEAD    # equal after the push, or it is not published yet
```
