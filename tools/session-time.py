#!/usr/bin/env python3
"""Where a session's wall-clock time went, read from the OpenCode database.

Method: one `session_part` row per tool call; a call lasts
`time_updated - time_created`. `active` is the span from the first tool call's
`time_created` to the last tool call's `time_updated` - the definition the
2026-11-24 baseline used for "first step to last step"; `wall` is the whole
session, including writing after the last call. Shares are taken against
`active`, so they compare with that baseline. `tools` is the sum of call
durations: parallel calls overlap, so it is not a partition of the span.

The database is opened read-only; nothing here writes to it.

    python tools/session-time.py --latest
    python tools/session-time.py --session ses_abc --slow 60
    python tools/session-time.py --session ses_abc --match mutate --match acceptance
    python tools/session-time.py --directory F:/work/project --json
"""

import argparse
import collections
import json
import os
import sqlite3
import sys


def default_db():
    base = os.environ.get("USERPROFILE") or os.path.expanduser("~")
    return os.path.join(base, ".local", "share", "opencode", "opencode.db")


def connect(path):
    return sqlite3.connect("file:" + os.path.abspath(path).replace("\\", "/") + "?mode=ro", uri=True)


def sessions_tree(c, root, with_children=True):
    if not with_children:
        return [root]
    rows = c.execute("select id, coalesce(parent_id, '') from session_v2").fetchall()
    children = collections.defaultdict(list)
    for sid, parent in rows:
        if parent:
            children[parent].append(sid)
    out, queue = [], [root]
    while queue:
        sid = queue.pop(0)
        out.append(sid)
        queue.extend(children.get(sid, []))
    return out


def pick_session(c, args):
    if args.session:
        row = c.execute("select id from session_v2 where id like ?", (args.session + "%",)).fetchone()
        if not row:
            sys.exit("no session matches " + args.session)
        return row[0]
    if args.directory:
        row = c.execute(
            "select id from session_v2 where coalesce(parent_id, '') = '' and directory like ?"
            " order by rowid desc limit 1", ("%" + args.directory.replace("\\", "/") + "%",)).fetchone()
        if not row:
            sys.exit("no root session in " + args.directory)
        return row[0]
    row = c.execute(
        "select session_id from session_part order by time_updated desc limit 1").fetchone()
    if not row:
        sys.exit("the database has no parts")
    return row[0]


def collect(c, session_ids):
    calls = []
    first = last = None
    tool_first = tool_last = None
    for sid in session_ids:
        for ptype, created, updated, data in c.execute(
                "select type, time_created, time_updated, data from session_part"
                " where session_id=?", (sid,)):
            first = created if first is None else min(first, created)
            last = updated if last is None else max(last, updated)
            if ptype != "tool":
                continue
            tool_first = created if tool_first is None else min(tool_first, created)
            tool_last = updated if tool_last is None else max(tool_last, updated)
            try:
                part = json.loads(data)
            except ValueError:
                continue
            state = part.get("state") or {}
            calls.append({
                "session": sid,
                "name": part.get("name") or "?",
                "seconds": round((updated - created) / 1000.0, 1),
                "input": state.get("input") or {},
                "status": state.get("status"),
            })
    wall = round((last - first) / 1000.0, 1) if first is not None else 0.0
    active = round((tool_last - tool_first) / 1000.0, 1) if tool_first is not None else 0.0
    return wall, active, calls


def short(call, width):
    inp = call["input"]
    text = inp.get("command") or inp.get("path") or inp.get("pattern") or ""
    text = " ".join(str(text).split())
    return text[:width]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--session", help="session id or unique prefix (default: newest)")
    ap.add_argument("--directory", help="newest root session whose directory contains this")
    ap.add_argument("--db", default=os.environ.get("OPENCODE_DB") or default_db())
    ap.add_argument("--slow", type=float, default=60.0, help="report calls at least this long, seconds")
    ap.add_argument("--top", type=int, default=10, help="longest calls to print, 0 to hide")
    ap.add_argument("--width", type=int, default=120, help="characters of a command in the top list")
    ap.add_argument("--match", action="append", default=[], help="regex over a shell command; repeatable")
    ap.add_argument("--no-children", action="store_true", help="ignore subagent sessions")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    c = connect(args.db)
    root = pick_session(c, args)
    ids = sessions_tree(c, root, not args.no_children)
    wall, active, calls = collect(c, ids)

    tools = collections.defaultdict(lambda: [0, 0.0])
    for call in calls:
        tools[call["name"]][0] += 1
        tools[call["name"]][1] += call["seconds"]
    shells = [call for call in calls if call["name"] == "shell"]
    shell = round(sum(call["seconds"] for call in shells), 1)
    slow = sorted([call for call in calls if call["seconds"] >= args.slow],
                  key=lambda call: -call["seconds"])
    title = c.execute("select title from session_v2 where id=?", (root,)).fetchone()
    title = title[0] if title else ""

    def share(part):
        return round(100.0 * part / active, 1) if active else 0.0

    if args.json:
        out = {
            "session": root,
            "title": title,
            "sessions": ids,
            "wall_seconds": wall,
            "active_seconds": active,
            "tool_seconds": round(sum(call["seconds"] for call in calls), 1),
            "shell_seconds": shell,
            "shell_calls": len(shells),
            "shell_share_of_active": share(shell),
            "tools": {name: {"calls": n, "seconds": round(s, 1)}
                      for name, (n, s) in sorted(tools.items(), key=lambda kv: -kv[1][1])},
            "slow_calls": [{"seconds": call["seconds"], "session": call["session"],
                            "tool": call["name"], "command": short(call, args.width)}
                           for call in slow],
            "matches": {},
        }
        for pattern in args.match:
            import re
            rx = re.compile(pattern, re.I)
            hit = [call for call in shells if rx.search(short(call, 10 ** 6))]
            out["matches"][pattern] = {"calls": len(hit),
                                       "seconds": round(sum(call["seconds"] for call in hit), 1)}
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    print("session  %s  %s" % (root, title))
    print("sessions %d (1 root + %d children)" % (len(ids), len(ids) - 1))
    print("wall     %8.1f s  %6.1f min  (whole session)" % (wall, wall / 60.0))
    print("active   %8.1f s  %6.1f min  (first tool to last tool = baseline span)"
          % (active, active / 60.0))
    print("tools    %8.1f s  %6.1f min  %5.1f%% of active  %d calls"
          % (sum(call["seconds"] for call in calls),
             sum(call["seconds"] for call in calls) / 60.0,
             share(sum(call["seconds"] for call in calls)), len(calls)))
    print("shell    %8.1f s  %6.1f min  %5.1f%% of active  %d calls"
          % (shell, shell / 60.0, share(shell), len(shells)))
    print()
    print("%-12s %7s %10s %9s" % ("tool", "calls", "seconds", "mean"))
    for name, (n, s) in sorted(tools.items(), key=lambda kv: -kv[1][1]):
        print("%-12s %7d %10.1f %9.1f" % (name, n, s, s / n))
    print()
    print("slow calls >= %.0f s: %d, %.1f s (%.1f min), %.1f%% of active"
          % (args.slow, len(slow), sum(call["seconds"] for call in slow),
             sum(call["seconds"] for call in slow) / 60.0,
             share(sum(call["seconds"] for call in slow))))
    if args.top and slow:
        print()
        for call in slow[:args.top]:
            print("%8.1f  %-4s  %s" % (call["seconds"], call["session"][-6:],
                                       short(call, args.width)))
    for pattern in args.match:
        import re
        rx = re.compile(pattern, re.I)
        hit = [call for call in shells if rx.search(short(call, 10 ** 6))]
        print("match %-20s %4d calls %9.1f s"
              % (pattern, len(hit), sum(call["seconds"] for call in hit)))


if __name__ == "__main__":
    main()
