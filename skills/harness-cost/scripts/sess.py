"""Per-session profile for OpenCode 2: tokens, steps, wall, tool calls.

Read-only. Usage (Windows: set PYTHONIOENCODING=utf-8 first):
  python sess.py --prefix ao-            # all titles starting with "ao-"
  python sess.py ab4-base ab5-snip       # titles containing the text (or session ids)
  python sess.py --id ses_xxx
  python sess.py --tools --prefix ab     # also dump every tool call: name, command, output head

Definitions:
  step   = assistant message with cost > 0 (billed)
  wall   = time_updated - time_created of the session row: elapsed, including idle gaps
  out    = tool output characters (len of the text parts), not bytes
"""
import sqlite3, os, sys, json, collections

DB = os.environ.get("OPENCODE_DB") or os.path.expandvars(
    r"%USERPROFILE%\.local\share\opencode\opencode.db")
c = sqlite3.connect("file:" + DB.replace("\\", "/") + "?mode=ro", uri=True)

args = sys.argv[1:]
dump_tools = "--tools" in args
args = [a for a in args if a != "--tools"]
sel = "like"
if args and args[0] == "--prefix":
    sel, args = "prefix", args[1:]
elif args and args[0] == "--id":
    sel, args = "id", args[1:]

cols = [d[1] for d in c.execute("pragma table_info(session_v2)")]
rows_out = []
for a in args:
    if sel == "id":
        rows_out += c.execute("select * from session_v2 where id = ?", (a,)).fetchall()
    elif sel == "prefix":
        rows_out += c.execute("select * from session_v2 where title like ?", (a + "%",)).fetchall()
    else:
        rows_out += c.execute("select * from session_v2 where title like ? or id = ?",
                              (a, a)).fetchall()
if not rows_out:
    raise SystemExit("no session matched " + repr(args))

tot = collections.Counter()
for s in rows_out:
    d = dict(zip(cols, s))
    sid = d["id"]
    steps, tools, tool_chars = [], collections.Counter(), 0
    for (data,) in c.execute(
            "select data from session_message where session_id=? and type='assistant' order by seq",
            (sid,)):
        m = json.loads(data)
        t = m.get("tokens") or {}
        if (m.get("cost") or 0) > 0:
            steps.append((((t.get("cache") or {}).get("read") or 0), t.get("input") or 0,
                          t.get("output") or 0))
        for p in m.get("content") or []:
            if p.get("type") != "tool":
                continue
            tools[p.get("name")] += 1
            st = p.get("state") or {}
            txt = "".join((ch.get("text") or "") for ch in (st.get("content") or []))
            tool_chars += len(txt)
            if dump_tools:
                inp = st.get("input") or {}
                print(f"   [{p.get('name')}] {st.get('status')} "
                      f"{str(inp.get('command') or inp.get('filePath') or inp)[:160]!r}")
                print(f"     out: {txt[:200].replace(chr(10), ' | ')!r}")
    n = len(steps)
    fr, ca, ou = (sum(x[i] for x in steps) for i in range(3))
    dur = (d["time_updated"] or 0) - (d["time_created"] or 0)
    print(f"== {d['title']}  [{sid}]")
    print(f"   dir={d['directory']}  parent={'yes' if d['parent_id'] else 'no'}")
    print(f"   steps={n}  fresh_in={fr:,}  cache_read={ca:,}  out={ou:,}  "
          f"session_tokens={fr+ca+ou:,}  cost={d['cost'] or 0:.4f}")
    if n:
        print(f"   per-step: fresh={fr//n:,} cache={ca//n:,} out={ou//n:,}")
    print(f"   wall={dur/1000:.0f}s  tools={dict(tools.most_common())}  tool_out_chars={tool_chars:,}")
    tot["steps"] += n; tot["fresh"] += fr; tot["cache"] += ca; tot["out"] += ou
    tot["cost"] += d["cost"] or 0; tot["wall"] += dur / 1000; tot["chars"] += tool_chars

print(f"-- TOTAL sessions={len(rows_out)} steps={tot['steps']} fresh={tot['fresh']:,} "
      f"cache={tot['cache']:,} out={tot['out']:,} "
      f"session_tokens={tot['fresh']+tot['cache']+tot['out']:,} "
      f"cost={tot['cost']:.4f} wall={tot['wall']:.0f}s tool_out_chars={tot['chars']:,}")
