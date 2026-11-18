"""Step 1b: why do `edit` calls fail? (read-only, one pass over the db)

  python editdiag.py [dir-prefix]     default: current directory

Prints: failure rate, error-message families, failed edits per session, file hotspots,
and read-output sizes / re-reads of the same path inside a session.
"""
import sqlite3, os, sys, json, collections, re

DB = os.environ.get("OPENCODE_DB") or os.path.expandvars(
    r"%USERPROFILE%\.local\share\opencode\opencode.db")
PREF = (sys.argv[1] if len(sys.argv) > 1 else os.getcwd()).replace("\\", "/").rstrip("/") + "%"
c = sqlite3.connect("file:" + DB.replace("\\", "/") + "?mode=ro", uri=True)

sess = list(c.execute(
    "select id, title, cost from session_v2 where directory like ? order by cost desc", (PREF,)))
top5 = {r[0] for r in sess[:5]}
print(f"sessions={len(sess)}  top5 by cost={[round(r[2] or 0, 2) for r in sess[:5]]}")


def family(msg):
    if isinstance(msg, dict):
        msg = msg.get("message") or json.dumps(msg, ensure_ascii=False)
    m = (msg or "").strip()
    m = re.sub(r"[A-Za-z]:\\[^\s'\"]+", "<path>", m)
    m = re.sub(r"line \d+", "line N", m)
    m = re.sub(r"\b\d+\b", "N", m)
    return m[:110].replace("\n", " | ")


edits = ok = 0
errs = collections.Counter()
err_examples = {}
per_session = collections.Counter()
hot = collections.Counter()
len_buckets = collections.Counter()
reads = collections.Counter()
read_sizes = []
rereads = collections.Counter()
err_text_ok = 0

for sid, title, cost in sess:
    seen_paths = collections.Counter()
    for (data,) in c.execute(
            "select data from session_message where session_id=? and type='assistant'", (sid,)):
        m = json.loads(data)
        for p in m.get("content") or []:
            if p.get("type") != "tool":
                continue
            st = p.get("state") or {}
            inp = st.get("input") or {}
            txt = "".join((ch.get("text") or "") for ch in (st.get("content") or []))
            name = p.get("name")
            if name == "edit":
                edits += 1
                if st.get("status") == "error":
                    per_session[(sid, title or "")] += 1
                    hot[inp.get("filePath")] += 1
                    f = family(st.get("error") or txt)
                    errs[f] += 1
                    err_examples.setdefault(f, str(st.get("error") or txt)[:300])
                    n = inp.get("oldString") or ""
                    len_buckets["<50" if len(n) < 50 else "50-200" if len(n) < 200
                               else "200-1000" if len(n) < 1000 else "1000+"] += 1
                else:
                    ok += 1
                    if re.search(r"not found|not unique|Failed", txt or "", re.I):
                        err_text_ok += 1
            elif name == "read":
                fp = inp.get("filePath") or inp.get("path") or ""
                reads[fp] += 1
                seen_paths[fp] += 1
                read_sizes.append(len(txt))

print(f"\nedit calls={edits}  ok={ok}  status=error={edits - ok} "
      f"({100 * (edits - ok) / max(1, edits):.1f}%)  "
      f"ok-but-error-text={err_text_ok}")
print(f"failed edits inside top5 sessions={sum(v for (s, t), v in per_session.items() if s in top5)} "
      f"of {edits - ok}")

print("\n-- error families")
for f, n in errs.most_common(12):
    print(f"  {n:4d}  {f}")
    print(f"        e.g. {err_examples[f].replace(chr(10), ' ')[:220]}")

print("\n-- oldString length of failed edits")
for k, n in len_buckets.items():
    print(f"  {k:>9}: {n}")

print("\n-- files with most failed edits")
for fp, n in hot.most_common(8):
    print(f"  {n:3d}  {fp}")

print("\n-- sessions with most failed edits")
for (sid, title), n in per_session.most_common(6):
    print(f"  {n:3d}  {'TOP5' if sid in top5 else '    '}  {title[:60]!r}")

sizes = sorted(read_sizes)
print(f"\n-- read outputs: n={len(sizes)}  median={sizes[len(sizes) // 2]:,} chars  "
      f"p90={sizes[int(len(sizes) * .9)]:,}  max={sizes[-1]:,}")
print(f"   >20k chars: {sum(1 for s in sizes if s > 20000)}  "
      f">40k: {sum(1 for s in sizes if s > 40000)}  "
      f"total chars={sum(sizes):,}")

print("\n-- most-read paths")
for fp, n in reads.most_common(10):
    print(f"  {n:4d}  {fp}")
