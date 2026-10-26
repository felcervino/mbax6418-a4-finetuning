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
            f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")).replace(" ", "\\u2028")
                    .replace(" ", "\\u2029") + "\n")


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
