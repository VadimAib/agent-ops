"""All numbers the report quotes, from one place, with one definition.

Step metric: billed assistant messages only (cost > 0).
  cache/step = sum(tokens.cache.read) / steps
  fresh/step = sum(tokens.input) / steps
  out/step   = sum(tokens.output) / steps
  reasoning  = sum(tokens.reasoning) (reported separately, not in the step metric)
Session-level totals (session_v2) are reported separately and labelled as such.

  python verify.py [dir-prefix]      default: current directory
"""
import sqlite3, os, sys, json, collections, statistics

DB = os.environ.get("OPENCODE_DB") or os.path.expandvars(
    r"%USERPROFILE%\.local\share\opencode\opencode.db")
PREF = (sys.argv[1] if len(sys.argv) > 1 else os.getcwd()).replace("\\", "/").rstrip("/") + "%"
c = sqlite3.connect("file:" + DB.replace("\\", "/") + "?mode=ro", uri=True)

ERR = ("ParserError", "CommandNotFoundException", "is not recognized",
       "UnicodeEncodeError", "Traceback (most recent call last)", "invalid-structure")

sess = list(c.execute(
    "select id,title,cost,tokens_cache_read,tokens_input,tokens_output,tokens_reasoning,"
    "parent_id,model,time_created,time_updated from session_v2 where directory like ?", (PREF,)))
paid = [s for s in sess if (s[2] or 0) > 0]
unpaid = [s for s in sess if not (s[2] or 0) > 0]
tok = lambda rs: sum((r[3] or 0) + (r[4] or 0) + (r[5] or 0) for r in rs)

if not sess:
    sys.exit(f"no sessions under {PREF.rstrip('%')}\n"
             "Pass the project directory: python verify.py F:/my-project")
if not paid:
    sys.exit(f"{len(sess)} sessions under {PREF.rstrip('%')}, none with cost > 0 (nothing billed)")

print("== 1. POPULATION")
print(f"sessions={len(sess)}  paid={len(paid)}  unpaid={len(unpaid)}")
print(f"tokens all(session-level, no reasoning)={tok(sess):,}  paid={tok(paid):,} "
      f"({100*tok(paid)/tok(sess):.1f}%)  unpaid={tok(unpaid):,} ({100*tok(unpaid)/tok(sess):.1f}%)")
print(f"cache share all sessions={100*sum(s[3] or 0 for s in sess)/tok(sess):.1f}%  "
      f"paid only={100*sum(s[3] or 0 for s in paid)/tok(paid):.1f}%")
print(f"cost paid={sum(s[2] for s in paid):.2f}  paid sessions with parent={sum(1 for s in paid if s[7])}  "
      f"unpaid with parent={sum(1 for s in unpaid if s[7])}")
print("paid models:", collections.Counter(
    json.loads(s[8]).get("providerID", "?") if s[8] else "?" for s in paid).most_common())
print("unpaid models:", collections.Counter(
    json.loads(s[8]).get("providerID", "?") if s[8] else "?" for s in unpaid).most_common())

print("\n== 2. PER-STEP, BILLED MESSAGES ONLY (paid sessions)")
rec = []
for s in paid:
    st = []
    for (d,) in c.execute("select data from session_message where session_id=? and type='assistant'",
                          (s[0],)):
        m = json.loads(d); t = m.get("tokens") or {}
        if (m.get("cost") or 0) > 0:
            st.append((((t.get("cache") or {}).get("read") or 0), t.get("input") or 0,
                       t.get("output") or 0, t.get("reasoning") or 0))
    rec.append(dict(steps=len(st), cache=sum(x[0] for x in st), fresh=sum(x[1] for x in st),
                    out=sum(x[2] for x in st), reas=sum(x[3] for x in st), cost=s[2],
                    parent=s[7] is not None, title=s[1]))
bins = [(1, 10), (10, 30), (30, 60), (60, 120), (120, 250), (250, 10**9)]
for label, sel in [("all", rec), ("root", [r for r in rec if not r["parent"]]),
                   ("child", [r for r in rec if r["parent"]])]:
    print(f"  -- {label}")
    for lo, hi in bins:
        b = [r for r in sel if lo <= r["steps"] < hi]
        st = sum(r["steps"] for r in b)
        if not st:
            continue
        cache = sum(r["cache"] for r in b); fresh = sum(r["fresh"] for r in b)
        out = sum(r["out"] for r in b); cost = sum(r["cost"] for r in b)
        print(f"   {lo}-{hi if hi < 10**8 else '+'}: n={len(b):2d} steps={st:4d} "
              f"cache/step={cache//st:7d} fresh/step={fresh//st:5d} out/step={out//st:4d} "
              f"cost/step={cost/st:.4f} cost/1M tok={cost/((cache+fresh+out)/1e6):.2f}")
tot_st = sum(r["steps"] for r in rec)
print(f"  total steps={tot_st} reasoning={sum(r['reas'] for r in rec):,} "
      f"output={sum(r['out'] for r in rec):,}")

print("\n== 3. THE FIVE LONGEST (cost share)")
rec2 = sorted(rec, key=lambda r: -r["cost"])[:5]
cs = sum(r["cost"] for r in rec2); ss = sum(r["steps"] for r in rec2)
print(f"cost {cs:.2f} of {sum(r['cost'] for r in rec):.2f} = {100*cs/sum(r['cost'] for r in rec):.1f}% | "
      f"steps {ss} of {tot_st} = {100*ss/tot_st:.1f}%")
for r in rec2:
    print(f"  {r['cost']:7.2f} steps={r['steps']:4d} root={not r['parent']} {r['title'][:40]!r}")

print("\n== 4. TOOLS AND FAILURES (all sessions in the directory)")
tools = collections.Counter(); errs = collections.Counter(); errs2 = collections.Counter()
big = []
for (sid, title) in [(s[0], s[1]) for s in sess]:
    for (d,) in c.execute("select data from session_message where session_id=? and type='assistant'",
                          (sid,)):
        for p in json.loads(d).get("content") or []:
            if p.get("type") != "tool":
                continue
            st = p.get("state") or {}
            txt = "".join((ch.get("text") or "") for ch in (st.get("content") or []))
            tools[p.get("name")] += 1
            if st.get("status") == "error":
                errs[p.get("name")] += 1
            if any(e in txt for e in ERR):
                errs2[p.get("name")] += 1
            big.append((len(txt), str(p.get("name")), str(title)))
print("tools:", dict(tools.most_common()))
print("status=error:", dict(errs))
print("error text in output:", dict(errs2.most_common()))
print("largest outputs:", [(n, t) for n, t, _ in sorted(big, reverse=True)[:5]])

print("\n== 5. A/B RUNS (all time, any directory)")
for (sid, title, directory, cost, t0, t1) in c.execute(
        "select id,title,directory,cost,time_created,time_updated from session_v2 "
        "where title like 'ab%' or title like '%prefix%' order by time_created"):
    st = []
    for (d,) in c.execute("select data from session_message where session_id=? and type='assistant'",
                          (sid,)):
        m = json.loads(d); t = m.get("tokens") or {}
        if (m.get("cost") or 0) > 0:
            st.append((((t.get("cache") or {}).get("read") or 0), t.get("input") or 0,
                       t.get("output") or 0))
    tt = sum(x[0] + x[1] + x[2] for x in st)
    print(f"  {title:22} steps={len(st):2d} tokens={tt:6d} per_step={tt//len(st) if st else 0:6d} "
          f"wall={(t1-t0)/1000:4.0f}s cost={cost or 0:6.4f} dir={os.path.basename(directory or '')}")
