"""Phase 1 data checks C-01..C-10 (+ anomaly report). Raises on any failure.

Usage: python tools/check_data.py [raw_gz] [split_zip] [out_prefix]
"""
import collections
import gzip
import hashlib
import json
import os
import sys
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import a4_helpers as h  # noqa: E402

RAW = sys.argv[1] if len(sys.argv) > 1 else "data/raw/Gift_Cards.jsonl.gz"
ZIP = sys.argv[2] if len(sys.argv) > 2 else "data/split_data.zip"
OUT = sys.argv[3] if len(sys.argv) > 3 else "evidence/gate_G1_data_checks"
FIELDS = ["original_row", "filtered_index", "title", "text", "rating", "reference_label"]

results = []


def check(cid, ok, detail):
    results.append({"id": cid, "pass": bool(ok), "detail": detail})
    print(f"{cid}: {'PASS' if ok else 'FAIL'} | {detail}")


def sha256(path):
    d = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            d.update(chunk)
    return d.hexdigest()


# ---- C-01 raw file
size = os.path.getsize(RAW)
digest = sha256(RAW)
lines = list(h.read_gz_lines(RAW))
check("C-01", len(lines) > 0, f"size={size} sha256={digest} physical_lines={len(lines)}")

# ---- anomaly scan on raw (reported verbatim, not fixed)
blank = [r for r, ln in lines if not ln.strip()]
short, nonstr_text, missing_text, nonstr_title, bad_rating = [], [], [], [], []
rating_types = collections.Counter()
rating_vals = collections.Counter()
for r, ln in lines:
    if not ln.strip():
        continue
    rec = json.loads(ln)
    t = rec.get("text")
    if "text" not in rec or t is None:
        missing_text.append(r)
    elif not isinstance(t, str):
        nonstr_text.append(r)
    elif len(t.strip()) < h.MIN_TEXT_CHARS:
        short.append(r)
    if not isinstance(rec.get("title", ""), (str, type(None))):
        nonstr_title.append(r)
    rt = rec.get("rating")
    rating_types[type(rt).__name__] += 1
    rating_vals[repr(rt)] += 1
    if rt not in (1, 2, 3, 4, 5):
        bad_rating.append(r)
print("ANOMALY blank_lines:", len(blank), blank[:10])
print("ANOMALY text_missing_or_None:", len(missing_text), missing_text[:10])
print("ANOMALY text_non_string:", len(nonstr_text), nonstr_text[:10])
print("ANOMALY text_too_short_after_strip:", len(short), short[:10])
print("ANOMALY title_non_string:", len(nonstr_title), nonstr_title[:10])
print("ANOMALY rating_outside_1_5:", len(bad_rating), bad_rating[:10])
print("rating python types:", dict(rating_types))
print("rating values:", dict(sorted(rating_vals.items())))

survivors = list(h.iter_survivors(lines))
gaps = collections.Counter()
for a, b in zip(survivors, survivors[1:]):
    gaps[b["original_row"] - a["original_row"]] += 1
print("survivors:", len(survivors), "last_original_row:", survivors[-1]["original_row"],
      "last_filtered_index:", survivors[-1]["filtered_index"])
print("original_row gap histogram (top 10):", gaps.most_common(10))
splits = h.build_splits(survivors)

# ---- load zip
zf = zipfile.ZipFile(ZIP)
zipped = {}
for k in ("train", "val", "test"):
    zipped[k] = [json.loads(x) for x in zf.read(f"{k}.jsonl").decode("utf-8").split("\n") if x.strip()]
print("zip sha256:", sha256(ZIP))

# ---- C-02 (filtered_index, original_row) pairs equal, per set
ok = True
detail = []
for k in splits:
    a = {(r["filtered_index"], r["original_row"]) for r in splits[k]}
    b = {(r["filtered_index"], r["original_row"]) for r in zipped[k]}
    detail.append(f"{k}: rebuilt={len(a)} zip={len(b)} equal={a == b}")
    ok &= a == b
check("C-02", ok, "; ".join(detail))

# ---- field-level equality by id (title, text, rating, label)
ok = True
detail = []
for k in splits:
    zr = {r["filtered_index"]: r for r in zipped[k]}
    mism = 0
    for r in splits[k]:
        z = zr[r["filtered_index"]]
        for fld in FIELDS:
            if r[fld] != z[fld]:
                mism += 1
                break
    detail.append(f"{k}: records_with_field_mismatch={mism}")
    ok &= mism == 0
check("C-02b", ok, "title/text/rating/label/original_row equal by id; " + "; ".join(detail))

# ---- C-03 labels recomputed from rating equal reference_label in the zip and rebuilt
bad = 0
for k in splits:
    for r in zipped[k] + splits[k]:
        if h.label_from_rating(r["rating"]) != r["reference_label"]:
            bad += 1
check("C-03", bad == 0, f"mismatches over zip+rebuilt rows: {bad}")

# ---- C-04 index ranges
rng = {"train": h.TRAIN_RANGE, "val": h.VAL_RANGE, "test": h.TEST_RANGE}
ok = all(rng[k][0] <= r["filtered_index"] <= rng[k][1] for k in rng for r in zipped[k] + splits[k])
check("C-04", ok, f"ranges {rng}")

# ---- C-05 train records AND order reproduced
same_order = [r["filtered_index"] for r in splits["train"]] == [r["filtered_index"] for r in zipped["train"]]
check("C-05", same_order, f"train order equal={same_order}; first 5 ids rebuilt="
      f"{[r['filtered_index'] for r in splits['train']][:5]} zip={[r['filtered_index'] for r in zipped['train']][:5]}")

# ---- C-06 / C-07 test and val are first 100 per class by file order (independent re-derivation from survivors)
for cid, k, (lo, hi) in (("C-06", "test", h.TEST_RANGE), ("C-07", "val", h.VAL_RANGE)):
    want = set()
    for c in h.LABELS:
        want |= set([s["filtered_index"] for s in survivors if lo <= s["filtered_index"] <= hi
                     and s["reference_label"] == c][:100])
    got = {r["filtered_index"] for r in zipped[k]}
    check(cid, want == got, f"{k}: zip ids equal first-100-per-class ids = {want == got}"
          + (" (static no-val-read scan is a notebook check, not done here)" if k == "val" else ""))

# ---- C-08 sizes and class counts
ok = True
detail = []
for k, n_cls in (("train", 300), ("val", 100), ("test", 100)):
    for name, src in (("zip", zipped[k]), ("rebuilt", splits[k])):
        cnt = collections.Counter(r["reference_label"] for r in src)
        detail.append(f"{k}/{name}: n={len(src)} {dict(cnt)}")
        ok &= len(src) == 3 * n_cls and all(cnt[c] == n_cls for c in h.LABELS)
check("C-08", ok, "; ".join(detail))

# ---- C-09 unique ids within each set
ok = all(len({r["filtered_index"] for r in s}) == len(s) and len({r["original_row"] for r in s}) == len(s)
         for s in list(zipped.values()) + list(splits.values()))
check("C-09", ok, "filtered_index and original_row unique within each set (zip and rebuilt)")

# ---- C-10 no shared ids across sets
ids = {k: {r["filtered_index"] for r in splits[k]} for k in splits}
ov = {f"{a}&{b}": len(ids[a] & ids[b]) for a, b in (("train", "val"), ("train", "test"), ("val", "test"))}
rows = {k: {r["original_row"] for r in splits[k]} for k in splits}
ovr = {f"{a}&{b}": len(rows[a] & rows[b]) for a, b in (("train", "val"), ("train", "test"), ("val", "test"))}
check("C-10", all(v == 0 for v in list(ov.values()) + list(ovr.values())),
      f"filtered_index overlaps {ov}; original_row overlaps {ovr}")

summary = {"raw_sha256": digest, "raw_size": size, "zip_sha256": sha256(ZIP), "physical_lines": len(lines),
           "survivors": len(survivors), "checks": results}
with open(OUT + ".json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=1)
failed = [r["id"] for r in results if not r["pass"]]
print("FAILED:", failed if failed else "none")
sys.exit(1 if failed else 0)
