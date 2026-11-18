"""Where the tokens go in a project: sessions by directory, tool histogram,
failed tool calls, biggest tool outputs. Read-only.

  python waste.py [dir ...]            default: current directory
"""
import sqlite3, os, sys, json, collections

DB = os.environ.get("OPENCODE_DB") or os.path.expandvars(
    r"%USERPROFILE%\.local\share\opencode\opencode.db")
c = sqlite3.connect("file:" + DB.replace("\\", "/") + "?mode=ro", uri=True)

dirs = [d.replace("\\", "/").rstrip("/") for d in (sys.argv[1:] or [os.getcwd()])]
for pref in dirs:
    sess = list(c.execute(
        "select id,title,time_created,time_updated,cost,tokens_input,tokens_cache_read,"
        "tokens_output,parent_id from session_v2 where directory like ?", (pref + "%",)))
    print(f"\n### {pref}: sessions={len(sess)} "
          f"cost={sum(s[4] or 0 for s in sess):.2f} "
          f"cache={sum(s[6] or 0 for s in sess):,} fresh={sum(s[5] or 0 for s in sess):,} "
          f"out={sum(s[7] or 0 for s in sess):,}")
    tools = collections.Counter()
    errs = collections.Counter()
    big = []
    steps_total = 0
    for sid, title, *_ in sess:
        steps = 0
        for (data,) in c.execute(
                "select data from session_message where session_id=? and type='assistant'",
                (sid,)):
            m = json.loads(data)
            if (m.get("cost") or 0) > 0:
                steps += 1
            for p in m.get("content") or []:
                if p.get("type") != "tool":
                    continue
                tools[p.get("name")] += 1
                st = p.get("state") or {}
                txt = "".join((ch.get("text") or "") for ch in (st.get("content") or []))
                if st.get("status") == "error":
                    errs[p.get("name")] += 1
                big.append((len(txt), str(p.get("name")), str(title), str(st.get("status"))))
        steps_total += steps
    print(f"  billed steps={steps_total} | tools={dict(tools.most_common(12))}")
    print(f"  failed tool calls={dict(errs)}")
    big.sort(reverse=True)
    print("  largest tool outputs:")
    for n, name, title, status in big[:8]:
        print(f"    {n:>7,} chars  {name}  status={status}  session={title!r}")

