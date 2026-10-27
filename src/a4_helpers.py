"""Helpers for MBAX 6418 Assignment 4 (pure Python plus numpy-free metrics).

Split builder, labels, prompt builders (provisional until Phase 2), strict label
parser, metrics, McNemar, prediction IO, adapter ZIP builder and verifier.
"""
import gzip
import hashlib
import json
import math
import os
import random
import re
import time
import urllib.error
import urllib.request
import uuid
import zipfile

LABELS = ["POSITIVE", "NEUTRAL", "NEGATIVE"]
CM_COLUMNS = LABELS + ["INVALID"]
PREDICTION_FIELDS = ["original_row", "filtered_index", "title", "text",
                     "reference_label", "prediction", "raw_response"]
ADAPTER_FILES = ["adapter_model.safetensors", "adapter_config.json"]

SYSTEM_PROMPT = ("You are an expert product review analyst. "
                 "Determine the sentiment each Amazon review expresses.")
USER_INSTRUCTION = ("Classify the sentiment of the review below as exactly one of: "
                    "POSITIVE, NEUTRAL, NEGATIVE. Reply with exactly one word, no explanation.")

MIN_TEXT_CHARS = 3
TRAIN_RANGE = (1000, 19999)
VAL_RANGE = (20000, 29999)
TEST_RANGE = (30000, 39999)
TRAIN_PER_CLASS = 300
EVAL_PER_CLASS = 100
TRAIN_SEED = 43
# One id per kernel start; stored with each hosted call so a resumed run shows which answers came from which session.
SESSION_ID = uuid.uuid4().hex


# ---------------------------------------------------------------- data

def read_gz_lines(path):
    """Yield (original_row, line) with 1-based physical line numbers; blank lines count."""
    with gzip.open(path, "rb") as f:
        for n, raw in enumerate(f, start=1):
            yield n, raw.decode("utf-8").rstrip("\n").rstrip("\r")


def label_from_rating(rating):
    if isinstance(rating, bool) or not isinstance(rating, (int, float)):
        raise ValueError(f"rating is not a number: {rating!r}")
    if isinstance(rating, float) and (math.isnan(rating) or rating != int(rating)):
        raise ValueError(f"rating is not a whole number: {rating!r}")
    r = int(rating)
    if r in (4, 5):
        return "POSITIVE"
    if r == 3:
        return "NEUTRAL"
    if r in (1, 2):
        return "NEGATIVE"
    raise ValueError(f"rating outside 1..5: {rating!r}")


def iter_survivors(lines):
    """lines: iterable of (original_row, line). Yields survivor dicts in file order."""
    idx = 0
    for row, line in lines:
        if not line.strip():
            continue
        rec = json.loads(line)
        text = rec.get("text")
        if text is None:
            text = ""
        if not isinstance(text, str):
            raise TypeError(f"row {row}: text is {type(text).__name__}, not str")
        if len(text.strip()) < MIN_TEXT_CHARS:
            continue
        title = rec.get("title")
        if title is None:
            title = ""
        if not isinstance(title, str):
            raise TypeError(f"row {row}: title is {type(title).__name__}, not str")
        rating = rec.get("rating")
        yield {"original_row": row, "filtered_index": idx, "title": title, "text": text,
               "rating": rating, "reference_label": label_from_rating(rating)}
        idx += 1


def build_splits(survivors):
    """Return {'train','val','test'} lists of records per PLAN 4.1."""
    survivors = list(survivors)
    by_idx_ok = [s for s in survivors]
    train_pool = {c: [s for s in by_idx_ok if TRAIN_RANGE[0] <= s["filtered_index"] <= TRAIN_RANGE[1]
                      and s["reference_label"] == c] for c in LABELS}
    for c in LABELS:
        if len(train_pool[c]) < TRAIN_PER_CLASS:
            raise ValueError(f"train pool for {c} has {len(train_pool[c])} < {TRAIN_PER_CLASS}")
    rng = random.Random(TRAIN_SEED)  # created once, used only here
    combined = []
    for c in LABELS:
        combined.extend(rng.sample(train_pool[c], TRAIN_PER_CLASS))
    rng.shuffle(combined)

    def first_per_class(lo, hi):
        out = []
        for c in LABELS:
            got = [s for s in by_idx_ok if lo <= s["filtered_index"] <= hi
                   and s["reference_label"] == c][:EVAL_PER_CLASS]
            if len(got) < EVAL_PER_CLASS:
                raise ValueError(f"range {lo}-{hi} class {c} has {len(got)} < {EVAL_PER_CLASS}")
            out.extend(got)
        return sorted(out, key=lambda s: s["filtered_index"])

    return {"train": combined, "val": first_per_class(*VAL_RANGE), "test": first_per_class(*TEST_RANGE)}


# ---------------------------------------------------------------- prompts (provisional, D-01/D-02 open)

def _user_turn(title, text):
    return f"{USER_INSTRUCTION}\n\nReview title: {title}\nReview text: {text}"


def build_messages_zero_shot(title, text):
    return [{"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _user_turn(title, text)}]


def build_messages_few_shot(title, text, examples):
    """examples: iterable of (title, text, label) in prompt order."""
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
    for ex_title, ex_text, ex_label in examples:
        if ex_label not in LABELS:
            raise ValueError(f"few-shot label not allowed: {ex_label!r}")
        msgs.append({"role": "user", "content": _user_turn(ex_title, ex_text)})
        msgs.append({"role": "assistant", "content": ex_label})
    msgs.append({"role": "user", "content": _user_turn(title, text)})
    return msgs


def build_messages_fine_tuned(title, text, target=None):
    msgs = build_messages_zero_shot(title, text)
    if target is not None:
        if target not in LABELS:
            raise ValueError(f"training target not allowed: {target!r}")
        msgs.append({"role": "assistant", "content": target})
    return msgs


def build_prompt_for_record(rec):
    """Only title and text are read from the record."""
    return build_messages_zero_shot(rec["title"], rec["text"])


def instruction_hash(messages):
    """Hash of the system text and the instruction line of the first user turn."""
    sys_txt = messages[0]["content"]
    first_user = next(m["content"] for m in messages if m["role"] == "user")
    instr = first_user.split("\n\nReview title:", 1)[0]
    return hashlib.sha256(json.dumps([sys_txt, instr]).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------- parsing and metrics

def parse_label(raw):
    if not isinstance(raw, str):
        return "INVALID"
    s = raw.strip().upper()
    return s if s in LABELS else "INVALID"


def confusion_matrix(refs, preds):
    if len(refs) != len(preds) or not refs:
        raise ValueError("refs and preds must be non-empty and equal length")
    cm = [[0] * len(CM_COLUMNS) for _ in LABELS]
    for r, p in zip(refs, preds):
        if r not in LABELS:
            raise ValueError(f"bad reference label {r!r}")
        if p not in CM_COLUMNS:
            raise ValueError(f"bad prediction {p!r}")
        cm[LABELS.index(r)][CM_COLUMNS.index(p)] += 1
    return cm


def normalize_rows(cm):
    out = []
    for row in cm:
        t = sum(row)
        out.append([v / t if t else 0.0 for v in row])
    return out


def compute_metrics(refs, preds):
    cm = confusion_matrix(refs, preds)
    per = {}
    pred_totals = [sum(cm[i][j] for i in range(3)) for j in range(3)]
    for i, c in enumerate(LABELS):
        n = sum(cm[i])
        tp = cm[i][i]
        rec = tp / n if n else 0.0
        prec = tp / pred_totals[i] if pred_totals[i] else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        per[c] = {"n": n, "correct": tp, "incorrect": n - tp, "predicted": pred_totals[i],
                  "precision": prec, "recall": rec, "f1": f1}
    correct = sum(v["correct"] for v in per.values())
    return {"per_class": per, "correct": correct, "incorrect": len(refs) - correct,
            "invalid": sum(row[3] for row in cm),
            "macro_f1": sum(v["f1"] for v in per.values()) / 3,
            "balanced_accuracy": sum(v["recall"] for v in per.values()) / 3,
            "confusion": cm}


def mcnemar_exact(b, c):
    from scipy.stats import binomtest
    from statsmodels.stats.contingency_tables import mcnemar
    n = b + c
    p_sm = float(mcnemar([[0, b], [c, 0]], exact=True).pvalue)
    # PLAN 4.6 cross-check: one-sided binomial tail doubled, capped at 1
    p_bin = 1.0 if n == 0 else min(1.0, 2 * float(
        binomtest(min(b, c), n, 0.5, alternative="less").pvalue))
    if not math.isclose(p_sm, p_bin, rel_tol=1e-9, abs_tol=1e-12):
        raise AssertionError(f"McNemar mismatch b={b} c={c}: statsmodels {p_sm} vs binomial {p_bin}")
    return {"b": b, "c": c, "p": p_sm, "p_statsmodels": p_sm, "p_binomial": p_bin}


def mcnemar_by_id(ref_by_id, pred1_by_id, pred2_by_id):
    """b = approach 1 correct and 2 wrong; c = 1 wrong and 2 correct. Aligned by id."""
    ids = set(ref_by_id)
    if set(pred1_by_id) != ids or set(pred2_by_id) != ids:
        raise ValueError("id sets differ between reference and predictions")
    b = c = 0
    for i in sorted(ids):
        ok1 = pred1_by_id[i] == ref_by_id[i]
        ok2 = pred2_by_id[i] == ref_by_id[i]
        b += ok1 and not ok2
        c += ok2 and not ok1
    return mcnemar_exact(b, c)


# ---------------------------------------------------------------- prediction IO and ZIP

def write_predictions(path, records):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in records:
            if list(r.keys()) != PREDICTION_FIELDS:
                raise ValueError(f"fields must be exactly {PREDICTION_FIELDS}, got {list(r.keys())}")
            f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")).replace("\u2028", "\\u2028")
                    .replace("\u2029", "\\u2029") + "\n")


def read_predictions(path):
    with open(path, "r", encoding="utf-8", newline="") as f:
        return [json.loads(line) for line in f.read().split("\n") if line]


def build_adapter_zip(paths, out_path):
    names = sorted(os.path.basename(p) for p in paths)
    if names != sorted(ADAPTER_FILES):
        raise ValueError(f"adapter ZIP must contain exactly {ADAPTER_FILES}, got {names}")
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in paths:
            z.write(p, arcname=os.path.basename(p))


def verify_adapter_zip(path):
    names = zipfile.ZipFile(path).namelist()
    if sorted(names) != sorted(ADAPTER_FILES):
        raise ValueError(f"ZIP namelist {names} != {ADAPTER_FILES}")
    return names


# ---------------------------------------------------------------- config hash

def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def sha256_hex(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def config_hash(cfg):
    return sha256_hex(canonical_json(cfg))


def frozen_hash(cfg, keys):
    return config_hash({k: cfg[k] for k in keys})


def messages_hash(messages):
    return config_hash(messages)


# ---------------------------------------------------------------- hosted calls

class TransportError(Exception):
    pass


def http_post_json(url, body, api_key, timeout):
    """POST JSON. Returns (status, raw_text). Raises TransportError on network failure or timeout."""
    req = urllib.request.Request(url, method="POST", data=json.dumps(body).encode("utf-8"),
                                 headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
        raise TransportError(f"{type(e).__name__}: {e}") from None


def _hosted_body(messages, cfg):
    return {"model": cfg["model"], "messages": messages, "temperature": cfg["temperature"],
            "max_tokens": cfg["max_tokens"], **cfg.get("extra_body", {})}


CACHE_WRITE_ATTEMPTS = 6


def _write_cache_file(path, rec, sleep=time.sleep):
    """Atomic cache write that survives a flaky (Drive-backed) folder.

    The hosted answer is already in memory, so a failed tmp-to-final rename is retried by rewriting the tmp file;
    the API is never called again for it. After the last attempt the error is raised, never swallowed.
    """
    for attempt in range(1, CACHE_WRITE_ATTEMPTS + 1):
        tmp = f"{path}.{uuid.uuid4().hex[:8]}.tmp"
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(rec, f, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, path)
            return
        except OSError:
            try:
                os.remove(tmp)
            except OSError:
                pass
            if attempt == CACHE_WRITE_ATTEMPTS:
                raise
            sleep(0.5 * attempt)


def call_hosted(messages, cfg, api_key, cache_dir, frozen, post=http_post_json, sleep=time.sleep):
    """One hosted chat call. Retries only transport errors and HTTP 5xx; never retries on content.

    The cache is keyed by sha256(frozen config hash + messages). First successful response wins.
    The API key is used only for the request header and is never stored.
    """
    os.makedirs(cache_dir, exist_ok=True)
    mh = messages_hash(messages)
    key = sha256_hex(frozen + "\n" + mh)
    path = os.path.join(cache_dir, key + ".json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            rec = json.load(f)
        rec["from_cache"] = True
        return rec
    body = _hosted_body(messages, cfg)
    url = cfg["base_url"].rstrip("/") + "/chat/completions"
    attempts = 0
    while True:
        attempts += 1
        t0 = time.perf_counter()
        try:
            status, raw = post(url, body, api_key, cfg["timeout_s"])
        except TransportError:
            if attempts > cfg["max_retries"]:
                raise
            sleep(cfg["retry_backoff_s"] * attempts)
            continue
        latency = time.perf_counter() - t0
        if status >= 500:
            if attempts > cfg["max_retries"]:
                raise RuntimeError(f"HTTP {status} after {attempts} attempts")
            sleep(cfg["retry_backoff_s"] * attempts)
            continue
        if status >= 400:
            raise RuntimeError(f"HTTP {status}: {raw[:200]}")
        break
    resp = json.loads(raw)
    choice = resp["choices"][0]
    msg = choice["message"]
    content = msg.get("content")
    reasoning = msg.get("reasoning") or msg.get("reasoning_content")
    usage = resp.get("usage") or {}
    rtok = (usage.get("completion_tokens_details") or {}).get("reasoning_tokens") or 0
    violations = []
    if choice.get("finish_reason") != "stop":
        violations.append(f"finish_reason:{choice.get('finish_reason')}")
    if reasoning:
        violations.append("reasoning_present")
    if rtok:
        violations.append(f"reasoning_tokens:{rtok}")
    rec = {"key": key, "messages_sha256": mh, "request_body": body, "raw": raw, "latency_s": latency,
           "http_status": status, "attempts": attempts, "content": content,
           "finish_reason": choice.get("finish_reason"), "completion_tokens": usage.get("completion_tokens"),
           "violations": violations, "prediction": parse_label(content), "from_cache": False,
           "session_id": SESSION_ID, "created_utc": time.time()}
    _write_cache_file(path, rec, sleep)
    return rec


# ---------------------------------------------------------------- data and prompt checks (each raises)

def fewshot_examples(train_by_id, ids):
    out = []
    for i in ids:
        r = train_by_id[i]
        out.append((r["title"], r["text"], r["reference_label"]))
    return out


def check_training_examples(examples, train_source, per_class=300):
    """C-11: the objects handed to the trainer are exactly the prescribed training rows."""
    src = {r["filtered_index"]: r for r in train_source}
    ids = [e["filtered_index"] for e in examples]
    assert len(ids) == len(set(ids)), "duplicate ids in training examples"
    assert set(ids) == set(src), "training example ids differ from the prescribed training ids"
    assert len(ids) == 3 * per_class, f"expected {3 * per_class} examples, got {len(ids)}"
    counts = {c: 0 for c in LABELS}
    for e in examples:
        assert set(e.keys()) == {"filtered_index", "messages"}, f"unexpected fields {sorted(e.keys())}"
        r = src[e["filtered_index"]]
        expected = build_messages_fine_tuned(r["title"], r["text"], target=r["reference_label"])
        assert e["messages"] == expected, f"messages differ from source for id {e['filtered_index']}"
        counts[r["reference_label"]] += 1
    assert all(v == per_class for v in counts.values()), f"class counts {counts}"
    return counts


def check_fewshot(ids, train_ids, reserved_ids, prompt_messages, train_by_id):
    """C-12: few-shot ids are train rows, disjoint from reserved sets, and match the prompt turns."""
    assert set(ids) <= set(train_ids), "few-shot id not in train"
    assert not (set(ids) & set(reserved_ids)), "few-shot id overlaps reserved ids"
    exs = fewshot_examples(train_by_id, ids)
    turns = build_messages_few_shot("", "", exs)[1:-1]
    assert len(prompt_messages) == len(turns) + 2, "prompt has the wrong number of turns"
    assert prompt_messages[1:-1] == turns, "few-shot turns in the prompt differ from the train records"


def check_one_prediction_per_id(preds_by_approach, test_ids):
    """C-13."""
    want = list(test_ids)
    for name, recs in preds_by_approach.items():
        got = [r["filtered_index"] for r in recs]
        assert len(got) == len(set(got)), f"{name}: duplicate ids"
        assert set(got) == set(want), f"{name}: id set differs from the test ids"
        assert len(got) == len(want), f"{name}: wrong count {len(got)}"


def check_instruction_identity(zero_shot, few_shot, fine_tuned):
    """C-14b."""
    hs = {instruction_hash(m) for m in (zero_shot, few_shot, fine_tuned)}
    assert len(hs) == 1, "instruction text differs across approaches"


def check_prompt_inputs(record, messages):
    """C-15: a built prompt contains only title and text from the record."""
    assert messages == build_messages_zero_shot(record["title"], record["text"]), "prompt is not a pure function of title and text"


def check_no_truncation(lengths, max_seq_length):
    """C-16."""
    assert max(lengths) <= max_seq_length, f"longest example {max(lengths)} > max_seq_length {max_seq_length}"


def check_predictions_records(records, test_ids):
    """C-19."""
    assert len(records) == len(test_ids), f"expected {len(test_ids)} rows, got {len(records)}"
    assert len({r["filtered_index"] for r in records}) == len(records), "duplicate ids"
    assert {r["filtered_index"] for r in records} == set(test_ids), "ids differ from the test ids"
    for r in records:
        assert list(r.keys()) == PREDICTION_FIELDS, f"field order {list(r.keys())}"
        assert r["prediction"] in LABELS + ["INVALID"], f"bad prediction {r['prediction']!r}"
        assert r["prediction"] == parse_label(r["raw_response"]), "prediction does not follow raw_response"
        assert r["reference_label"] in LABELS


def check_prompt_examples(records, expected_messages_by_id):
    """C-20: 3 rows, one per class, messages equal the rebuilt prompt, no label inside messages."""
    assert len(records) == 3, f"expected 3 rows, got {len(records)}"
    assert sorted(r["reference_label"] for r in records) == sorted(LABELS), "not one row per class"
    for r in records:
        assert r["messages"] == expected_messages_by_id[r["filtered_index"]], "messages differ from rebuilt prompt"
        assert all(m["role"] != "assistant" for m in r["messages"]), "assistant turn (label) inside messages"


def scan_forbidden_tokens(sources, patterns):
    """Static scan used for C-07 and the sealed test labels: raise if any pattern occurs."""
    for i, src in enumerate(sources):
        for pat in patterns:
            m = re.search(pat, src)
            assert not m, f"forbidden pattern {pat!r} in source {i} near: {src[max(0, m.start() - 30):m.end() + 30]!r}"


# ---------------------------------------------------------------- in-notebook data checks C-02..C-10

def read_zip_splits(zip_path):
    with zipfile.ZipFile(zip_path) as z:
        return {k: [json.loads(x) for x in z.read(f"{k}.jsonl").decode("utf-8").split("\n") if x.strip()]
                for k in ("train", "val", "test")}


def run_data_checks(survivors, splits, zipped):
    """Port of tools/check_data.py (C-02..C-10). Returns a list of result dicts; raises on any failure."""
    fields = ["original_row", "filtered_index", "title", "text", "rating", "reference_label"]
    res = []

    def check(cid, ok, detail):
        res.append({"id": cid, "pass": bool(ok), "detail": detail})

    check("C-02", all({(r["filtered_index"], r["original_row"]) for r in splits[k]} ==
                      {(r["filtered_index"], r["original_row"]) for r in zipped[k]} for k in splits),
          "(filtered_index, original_row) pairs equal the zip for train, val, test")
    mism = 0
    for k in splits:
        zr = {r["filtered_index"]: r for r in zipped[k]}
        for r in splits[k]:
            z = zr[r["filtered_index"]]
            mism += any(r[f] != z[f] for f in fields)
    check("C-02b", mism == 0, f"records with a field mismatch vs zip: {mism}")
    bad = sum(label_from_rating(r["rating"]) != r["reference_label"] for k in splits for r in zipped[k] + splits[k])
    check("C-03", bad == 0, f"label/rating mismatches: {bad}")
    rng = {"train": TRAIN_RANGE, "val": VAL_RANGE, "test": TEST_RANGE}
    check("C-04", all(rng[k][0] <= r["filtered_index"] <= rng[k][1] for k in rng for r in zipped[k] + splits[k]),
          f"ranges {rng}")
    check("C-05", [r["filtered_index"] for r in splits["train"]] == [r["filtered_index"] for r in zipped["train"]],
          "train records and ORDER reproduced from Random(43)")
    for cid, k, (lo, hi) in (("C-06", "test", TEST_RANGE), ("C-07a", "val", VAL_RANGE)):
        want = set()
        for c in LABELS:
            want |= set([s["filtered_index"] for s in survivors if lo <= s["filtered_index"] <= hi
                         and s["reference_label"] == c][:EVAL_PER_CLASS])
        check(cid, want == {r["filtered_index"] for r in zipped[k]}, f"{k} = first {EVAL_PER_CLASS} per class in file order")
    ok = True
    parts = []
    for k, n in (("train", TRAIN_PER_CLASS), ("val", EVAL_PER_CLASS), ("test", EVAL_PER_CLASS)):
        for name, src in (("zip", zipped[k]), ("rebuilt", splits[k])):
            cnt = {c: sum(r["reference_label"] == c for r in src) for c in LABELS}
            ok &= len(src) == 3 * n and all(v == n for v in cnt.values())
            parts.append(f"{k}/{name}: n={len(src)} {cnt}")
    check("C-08", ok, "; ".join(parts))
    check("C-09", all(len({r["filtered_index"] for r in s}) == len(s) and len({r["original_row"] for r in s}) == len(s)
                      for s in list(zipped.values()) + list(splits.values())), "unique ids within each set")
    ids = {k: {r["filtered_index"] for r in splits[k]} for k in splits}
    ov = {f"{a}&{b}": len(ids[a] & ids[b]) for a, b in (("train", "val"), ("train", "test"), ("val", "test"))}
    check("C-10", all(v == 0 for v in ov.values()), f"overlaps {ov}")
    failed = [r["id"] for r in res if not r["pass"]]
    assert not failed, f"data checks failed: {failed}"
    return res


# ---------------------------------------------------------------- results helpers (S8)

def best_approach(metrics_by_name):
    """Highest macro-F1; tie-break higher balanced accuracy, then alphabetical name (declared in PLAN 4.6)."""
    return sorted(metrics_by_name, key=lambda n: (-metrics_by_name[n]["macro_f1"],
                                                  -metrics_by_name[n]["balanced_accuracy"], n))[0]


def error_analysis(ref_by_id, zero_by_id, few_by_id, ft_by_id, n=10):
    """First n ids (by filtered_index) in each list. Rule fixed in advance (DEC-07)."""
    ids = sorted(ref_by_id)

    def ok(pred, i):
        return pred[i] == ref_by_id[i]

    fixed = [i for i in ids if ok(ft_by_id, i) and not ok(zero_by_id, i) and not ok(few_by_id, i)]
    broken = [i for i in ids if not ok(ft_by_id, i) and ok(zero_by_id, i) and ok(few_by_id, i)]
    wrong_all = [i for i in ids if not ok(ft_by_id, i) and not ok(zero_by_id, i) and not ok(few_by_id, i)]
    return {"fixed_by_ft": {"total": len(fixed), "ids": fixed[:n]},
            "broken_by_ft": {"total": len(broken), "ids": broken[:n]},
            "wrong_in_all": {"total": len(wrong_all), "ids": wrong_all[:n]}}


# Phase 2 rule (tools/phase2_shortlist.py), reused for the optional title-leakage analysis.
STAR_TITLE = re.compile(r"^\s*(\w+\s+)?(\d|one|two|three|four|five)\s+stars?\b", re.I)


def is_star_title(title):
    return bool(STAR_TITLE.match(title or ""))


def star_title_breakdown(ref_by_id, title_by_id, preds_by_name):
    """Descriptive only: correct counts on star-word titles vs the other titles, overall and within each reference
    class (the class mix differs between the two groups). INVALID counts as wrong. Never used to tune."""
    ids = sorted(ref_by_id)
    star = [i for i in ids if is_star_title(title_by_id[i])]
    rest = [i for i in ids if not is_star_title(title_by_id[i])]

    def mix(sub):
        return {c: sum(ref_by_id[i] == c for i in sub) for c in LABELS}

    def acc(pred, sub):
        n_ok = sum(pred[i] == ref_by_id[i] for i in sub)
        return n_ok, (n_ok / len(sub) if sub else None)

    by = {}
    for n in sorted(preds_by_name):
        p = preds_by_name[n]
        sc, sa = acc(p, star)
        rc, ra = acc(p, rest)
        per = {}
        for c in LABELS:
            s_c, r_c = [i for i in star if ref_by_id[i] == c], [i for i in rest if ref_by_id[i] == c]
            (s_ok, s_rec), (r_ok, r_rec) = acc(p, s_c), acc(p, r_c)
            per[c] = {"star_n": len(s_c), "star_correct": s_ok, "star_recall": s_rec,
                      "rest_n": len(r_c), "rest_correct": r_ok, "rest_recall": r_rec}
        by[n] = {"star_correct": sc, "star_accuracy": sa, "rest_correct": rc, "rest_accuracy": ra, "per_class": per}
    return {"n_star": len(star), "n_rest": len(rest), "star_ids": star,
            "star_label_mix": mix(star), "rest_label_mix": mix(rest), "by_approach": by}


def flip_sample(train_rows, exclude_ids, per_class, seed):
    """DEC-05: per_class TRAIN ids per class (exclusions removed), one RNG over classes in LABELS order, sorted output."""
    rng = random.Random(seed)
    excl = set(exclude_ids)
    out = []
    for c in LABELS:
        pool = sorted(r["filtered_index"] for r in train_rows if r["reference_label"] == c and r["filtered_index"] not in excl)
        assert len(pool) >= per_class, f"flip sample: only {len(pool)} {c} rows"
        out += rng.sample(pool, per_class)
    return sorted(out)


def repeat_hosted(messages, cfg, api_key, cache_root, frozen, repeats, post=http_post_json, sleep=time.sleep):
    """DEC-05: `repeats` independent calls for one prompt. Each repeat has its own cache folder, so the calls are
    separate requests, while a restart resumes from saved responses instead of re-rolling them."""
    return [call_hosted(messages, cfg, api_key, os.path.join(cache_root, f"rep{k}"), frozen, post=post, sleep=sleep)
            for k in range(1, repeats + 1)]


def flip_rate(reps_by_id):
    """reps_by_id: id -> list of (prediction, raw content), one per repeat. A flip = not all repeats identical."""
    counts = {len(v) for v in reps_by_id.values()}
    assert len(counts) <= 1, f"uneven repeats: {counts}"
    ids = sorted(reps_by_id)
    label_flips = [i for i in ids if len({p for p, _ in reps_by_id[i]}) > 1]
    raw_flips = [i for i in ids if len({r for _, r in reps_by_id[i]}) > 1]
    return {"items": len(ids), "repeats": counts.pop() if counts else 0, "label_flips": len(label_flips),
            "label_flip_ids": label_flips, "label_flip_rate": len(label_flips) / len(ids) if ids else None, "raw_flips": len(raw_flips), "raw_flip_ids": raw_flips,
            "invalid_responses": sum(p == "INVALID" for v in reps_by_id.values() for p, _ in v)}


def flip_summary(raw_records, approaches):
    """DEC-05 result rebuilt from the saved flip records (S4b writes them, S10 re-reads them after any restart).
    mixed_session_ids: prompts whose repeats were answered in different kernel sessions (a resumed run)."""
    out = {}
    for a in approaches:
        recs = [r for r in raw_records if r["approach"] == a]
        ids = sorted({r["filtered_index"] for r in recs})
        reps, sessions = {}, {}
        for i in ids:
            rs = sorted((r for r in recs if r["filtered_index"] == i), key=lambda r: r["repeat"])
            assert [r["repeat"] for r in rs] == list(range(1, len(rs) + 1)), f"{a} id {i}: repeats {[r['repeat'] for r in rs]}"
            reps[i] = [(r["prediction"], r["raw_response"]) for r in rs]
            sessions[i] = {r["session_id"] for r in rs}
        res = flip_rate(reps)
        res.update({"calls": len(recs), "cache_hits": sum(bool(r["from_cache"]) for r in recs),
                    "calls_with_violations": sum(bool(r["violations"]) for r in recs),
                    "sum_latency_s": round(sum(r["latency_s"] for r in recs), 3),
                    "mixed_session_ids": [i for i in ids if len(sessions[i]) > 1]})
        out[a] = res
    return out


def pairwise_mcnemar(ref_by_id, preds_by_name):
    names = sorted(preds_by_name)
    out = {}
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            out[f"{a} vs {b}"] = mcnemar_by_id(ref_by_id, preds_by_name[a], preds_by_name[b])
    return out


# ---------------------------------------------------------------- chat text for training, prefix check, canonical prompts

def render_chat_text(tok, messages, strip_bos=True):
    """Chat-template text for training. Some templates emit BOS as text while the tokenizer adds BOS again."""
    t = tok.apply_chat_template(messages, tokenize=False)
    if strip_bos and getattr(tok, "bos_token", None) and t.startswith(tok.bos_token):
        t = t[len(tok.bos_token):]
    return t


def check_prompt_is_training_prefix(prompt_ids, train_ids):
    """R-19: the token ids of the inference prompt are exactly the start of the training example's ids (single BOS)."""
    prompt_ids, train_ids = list(prompt_ids), list(train_ids)
    assert len(prompt_ids) < len(train_ids), "training example is not longer than its prompt"
    assert train_ids[:len(prompt_ids)] == prompt_ids, "inference prompt tokens are not a prefix of the training tokens"


def canonical_prompt_fingerprint(fewshot):
    """Rendered prompts for fixed synthetic inputs plus the parser table, so any drift in the helpers changes the freeze hash."""
    probe = ["POSITIVE", " neutral\n", "Positive.", "", "POSITIVE NEGATIVE", None]
    return {"zero_shot": build_messages_zero_shot(" T ", "Line1\nLine2 "),
            "few_shot": build_messages_few_shot(" T ", "Line1\nLine2 ", fewshot),
            "fine_tuned": build_messages_fine_tuned(" T ", "Line1\nLine2 ", target="NEUTRAL"),
            "parse_table": [parse_label(x) for x in probe]}
