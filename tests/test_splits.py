import gzip
import json
import random

import pytest

import a4_helpers as h


def _write_gz(path, lines):
    with gzip.open(path, "wb") as f:
        for ln in lines:
            f.write(ln.encode("utf-8") + b"\n")


def _rec(rating, text, title="t"):
    return json.dumps({"rating": rating, "title": title, "text": text})


# T-01 builder on a synthetic file
def test_t01_survivors_blank_short_missing(tmp_path):
    p = tmp_path / "s.jsonl.gz"
    lines = [
        _rec(5.0, "great card"),                          # row 1 -> idx 0
        "",                                               # row 2 blank
        _rec(4.0, "ok"),                                  # row 3 2 chars, skipped
        _rec(3.0, "   x  "),                              # row 4 1 char after strip, skipped
        json.dumps({"rating": 1.0, "title": "no text"}),  # row 5 missing text, skipped
        json.dumps({"rating": 2.0, "title": "n", "text": None}),  # row 6 None, skipped
        "   ",                                            # row 7 whitespace-only line
        _rec(1.0, "bad one", title=""),                   # row 8 -> idx 1, empty title kept
        _rec(3.0, "  abc  "),                             # row 9 -> idx 2, 3 chars kept
    ]
    _write_gz(p, lines)
    surv = list(h.iter_survivors(h.read_gz_lines(str(p))))
    assert [(s["original_row"], s["filtered_index"]) for s in surv] == [(1, 0), (8, 1), (9, 2)]
    assert [s["reference_label"] for s in surv] == ["POSITIVE", "NEGATIVE", "NEUTRAL"]
    assert surv[1]["title"] == ""
    assert surv[2]["text"] == "  abc  "  # stored unmodified


def test_t01_non_string_text_reported():
    with pytest.raises(TypeError):
        list(h.iter_survivors([(1, _rec(5.0, 123))]))


def test_t01_missing_title_is_not_filtered():
    surv = list(h.iter_survivors([(1, json.dumps({"rating": 5.0, "text": "good one"}))]))
    assert len(surv) == 1 and surv[0]["title"] == ""


# T-02 label boundaries
@pytest.mark.parametrize("r,lab", [(1, "NEGATIVE"), (2, "NEGATIVE"), (3, "NEUTRAL"),
                                   (4, "POSITIVE"), (5, "POSITIVE"), (5.0, "POSITIVE"), (3.0, "NEUTRAL")])
def test_t02_labels(r, lab):
    assert h.label_from_rating(r) == lab


@pytest.mark.parametrize("r", [0, 6, 2.5, -1, None, "5", float("nan"), True])
def test_t02_invalid_ratings_raise(r):
    with pytest.raises(ValueError):
        h.label_from_rating(r)


def _synthetic_survivors():
    """Survivors for indices 0..39999 with a deterministic label pattern."""
    pat = [5.0, 3.0, 1.0, 4.0, 3.0, 2.0, 5.0]
    out = []
    for i in range(40000):
        r = pat[i % len(pat)]
        out.append({"original_row": i + 1 + i // 50, "filtered_index": i, "title": f"t{i}",
                    "text": f"text {i}", "rating": r, "reference_label": h.label_from_rating(r)})
    return out


def test_build_splits_structure():
    surv = _synthetic_survivors()
    s = h.build_splits(surv)
    assert [len(s[k]) for k in ("train", "val", "test")] == [900, 300, 300]
    for k, (lo, hi) in (("train", (1000, 19999)), ("val", (20000, 29999)), ("test", (30000, 39999))):
        assert all(lo <= r["filtered_index"] <= hi for r in s[k])
    for k, lo in (("val", 20000), ("test", 30000)):
        for c in h.LABELS:
            got = [r["filtered_index"] for r in s[k] if r["reference_label"] == c]
            want = [r["filtered_index"] for r in surv
                    if lo <= r["filtered_index"] <= lo + 9999 and r["reference_label"] == c][:100]
            assert got == want
    # train procedure: Random(43) once, sample per class in fixed order, then shuffle
    rng = random.Random(43)
    comb = []
    for c in ("POSITIVE", "NEUTRAL", "NEGATIVE"):
        pool = [r for r in surv if 1000 <= r["filtered_index"] <= 19999 and r["reference_label"] == c]
        comb += rng.sample(pool, 300)
    rng.shuffle(comb)
    assert [r["filtered_index"] for r in comb] == [r["filtered_index"] for r in s["train"]]


def test_build_splits_short_pool_raises():
    with pytest.raises(ValueError):
        h.build_splits(_synthetic_survivors()[:25000])
