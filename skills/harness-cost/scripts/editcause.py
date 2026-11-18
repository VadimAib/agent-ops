"""Step 1c: classify the 214 failed edits and test the likely cause (read-only).

  python editcause.py [dir-prefix]   default: current directory

For every failed edit: cause bucket, input key names, and whether the current file
still contains oldString — exactly, with LF-normalised line endings, or with all
whitespace collapsed. The last two separate "line-ending/whitespace artifact" from
"the content really changed since the model read it".
"""
import sqlite3, os, sys, json, collections, re

DB = os.environ.get("OPENCODE_DB") or os.path.expandvars(
    r"%USERPROFILE%\.local\share\opencode\opencode.db")
PREF = (sys.argv[1] if len(sys.argv) > 1 else os.getcwd()).replace("\\", "/").rstrip("/") + "%"
c = sqlite3.connect("file:" + DB.replace("\\", "/") + "?mode=ro", uri=True)


def cause(msg):
    m = msg if isinstance(msg, str) else json.dumps(msg, ensure_ascii=False)
    if "Could not find oldString" in m:
        return "not-found"
    if "No changes to apply" in m:
        return "no-op (identical)"
    if "File not found" in m:
        return "bad path"
    if "matches for oldString" in m:
        return "not unique"
    if "Invalid arguments" in m:
        return "bad arguments"
    return "other"


def path_of(msg, inp):
    m = msg["message"] if isinstance(msg, dict) else (msg or "")
    ext = r"\.(?:py|html|md|json|yaml|yml|js|css|txt|ts|sh)"
    hit = (re.search(r"[A-Za-z]:\\[^\n]*?" + ext, m)
           or re.search(r"(?<![\w:/])[\w./\\-]+" + ext, m))
    if hit:
        p = hit.group(0)
        if not re.match(r"^[A-Za-z]:", p):
            p = os.path.join(PREF.rstrip("%").rstrip("/").replace("/", "\\"), p.replace("/", "\\"))
        return p
    for k in ("path", "filePath"):
        if inp.get(k):
            return inp[k]
    return "?"


buckets = collections.Counter()
keys = collections.Counter()
paths = collections.Counter()
rows = []
for (sid,) in c.execute("select id from session_v2 where directory like ?", (PREF,)):
    for (data,) in c.execute(
            "select data from session_message where session_id=? and type='assistant'", (sid,)):
        for p in json.loads(data).get("content") or []:
            if p.get("type") != "tool" or p.get("name") != "edit":
                continue
            st = p.get("state") or {}
            if st.get("status") != "error":
                continue
            inp = st.get("input") or {}
            err = st.get("error")
            buckets[cause(err)] += 1
            keys[",".join(sorted(inp.keys()))] += 1
            paths[path_of(err, inp)] += 1
            rows.append((sid, path_of(err, inp), inp.get("oldString") or ""))

total = sum(buckets.values())
print(f"failed edits={total}")
print("\n-- cause")
for k, n in buckets.most_common():
    print(f"  {n:4d}  {100*n/total:5.1f}%  {k}")
print("\n-- input keys")
for k, n in keys.most_common():
    print(f"  {n:4d}  {k}")
print("\n-- files (top 8)")
for k, n in paths.most_common(8):
    print(f"  {n:4d}  {k}")

print("\n-- does the current file still contain oldString?")
res = collections.Counter()
for sid, path, old in rows:
    if not path or not os.path.isfile(path) or not old:
        res["file missing / empty oldString"] += 1
        continue
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            body = f.read()
    except OSError:
        res["file unreadable"] += 1
        continue
    if old in body:
        res["exact match now"] += 1
    elif old.replace("\r\n", "\n") in body.replace("\r\n", "\n"):
        res["match after LF normalisation"] += 1
    elif re.sub(r"\s+", " ", old).strip() in re.sub(r"\s+", " ", body):
        res["match after whitespace collapse"] += 1
    else:
        res["no match (content changed)"] += 1
for k, n in res.most_common():
    print(f"  {n:4d}  {k}")

print("\n-- line endings under the prefix")
crlf = lf = 0
for root, dirs, files in os.walk(PREF.rstrip("%").rstrip("/")):
    dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", "node_modules", ".venv")]
    for fn in files:
        if not fn.endswith((".py", ".html", ".md", ".json", ".yaml", ".yml", ".js", ".css")):
            continue
        try:
            b = open(os.path.join(root, fn), "rb").read()
        except OSError:
            continue
        if b"\r\n" in b:
            crlf += 1
        elif b"\n" in b:
            lf += 1
print(f"  CRLF files={crlf}  LF files={lf}")
