"""Title-leakage analysis and DEC-05 flip-rate measurement (designs approved by Felipe 2026-10-26)."""
import json

import pytest

import a4_helpers as h
from test_hosted import CFG, MSGS, FakePost, _resp


def test_star_title_regex_is_the_phase2_rule():
    assert h.STAR_TITLE.pattern == r"^\s*(\w+\s+)?(\d|one|two|three|four|five)\s+stars?\b"
    for t in ["Five Stars", "five stars", " 4 Star", "Great 5 stars", "One star", "Five star service"]:
        assert h.is_star_title(t), t
    for t in ["Stars", "Love it", "Five", "Really great five stars", "5stars", "Fivestars", ""]:
        assert not h.is_star_title(t), t


def test_title_leakage_counts_and_accuracy():
    ref = {1: "POSITIVE", 2: "NEGATIVE", 3: "NEUTRAL", 4: "POSITIVE", 5: "NEGATIVE"}
    titles = {1: "Five Stars", 2: "One Star", 3: "meh", 4: "Love it", 5: "Two stars"}
    preds = {"a": {1: "POSITIVE", 2: "NEUTRAL", 3: "NEUTRAL", 4: "INVALID", 5: "NEGATIVE"},
             "b": {1: "POSITIVE", 2: "NEGATIVE", 3: "POSITIVE", 4: "POSITIVE", 5: "NEGATIVE"}}
    out = h.star_title_breakdown(ref, titles, preds)
    assert out["n_star"] == 3 and out["n_rest"] == 2
    assert out["star_ids"] == [1, 2, 5]
    assert out["star_label_mix"] == {"POSITIVE": 1, "NEUTRAL": 0, "NEGATIVE": 2}
    assert out["rest_label_mix"] == {"POSITIVE": 1, "NEUTRAL": 1, "NEGATIVE": 0}
    a, b = out["by_approach"]["a"], out["by_approach"]["b"]
    assert (a["star_correct"], a["star_accuracy"], a["rest_correct"], a["rest_accuracy"]) == (2, 2 / 3, 1, 0.5)
    assert (b["star_correct"], b["star_accuracy"], b["rest_correct"], b["rest_accuracy"]) == (3, 1.0, 1, 0.5)
    # within-class split (red-team P1-5): class mix differs between the groups, so compare inside each class
    assert a["per_class"]["NEGATIVE"] == {"star_n": 2, "star_correct": 1, "star_recall": 0.5,
                                          "rest_n": 0, "rest_correct": 0, "rest_recall": None}
    assert a["per_class"]["POSITIVE"] == {"star_n": 1, "star_correct": 1, "star_recall": 1.0,
                                          "rest_n": 1, "rest_correct": 0, "rest_recall": 0.0}
    assert b["per_class"]["NEUTRAL"] == {"star_n": 0, "star_correct": 0, "star_recall": None,
                                         "rest_n": 1, "rest_correct": 0, "rest_recall": 0.0}


def test_title_leakage_empty_subset_gives_none():
    out = h.star_title_breakdown({1: "POSITIVE"}, {1: "fine"}, {"a": {1: "POSITIVE"}})
    assert out["n_star"] == 0 and out["by_approach"]["a"]["star_accuracy"] is None
    assert out["by_approach"]["a"]["rest_accuracy"] == 1.0


def _train(n_per_class=15):
    rows, i = [], 1000
    for c in h.LABELS:
        for _ in range(n_per_class):
            rows.append({"filtered_index": i, "reference_label": c})
            i += 1
    return rows


def test_flip_sample_rule():
    train = _train()
    exclude = [1000, 1015, 1030]
    ids = h.flip_sample(train, exclude, per_class=10, seed=20261029)
    assert ids == sorted(ids) and len(ids) == 30 and len(set(ids)) == 30
    assert not set(ids) & set(exclude)
    by_id = {r["filtered_index"]: r["reference_label"] for r in train}
    assert all(sum(by_id[i] == c for i in ids) == 10 for c in h.LABELS)
    assert ids == h.flip_sample(list(reversed(train)), exclude, per_class=10, seed=20261029)  # input order does not matter
    assert ids != h.flip_sample(train, exclude, per_class=10, seed=1)


def test_flip_sample_too_small_pool_raises():
    with pytest.raises(AssertionError):
        h.flip_sample(_train(5), [], per_class=10, seed=20261029)


def test_repeat_hosted_makes_independent_calls_and_resumes(tmp_path):
    fp = FakePost([(200, _resp("POSITIVE")), (200, _resp("NEUTRAL")), (200, _resp("POSITIVE"))])
    recs = h.repeat_hosted(MSGS, CFG, "KEY", str(tmp_path), "frozen1", repeats=3, post=fp)
    assert [r["prediction"] for r in recs] == ["POSITIVE", "NEUTRAL", "POSITIVE"]
    assert len(fp.calls) == 3 and not any(r["from_cache"] for r in recs)
    again = h.repeat_hosted(MSGS, CFG, "KEY", str(tmp_path), "frozen1", repeats=3, post=FakePost([]))
    assert [r["prediction"] for r in again] == ["POSITIVE", "NEUTRAL", "POSITIVE"]  # a restart resumes, never re-rolls
    assert all(r["from_cache"] for r in again)
    assert "KEY" not in json.dumps([r for r in again])


def test_flip_rate_summary():
    reps = {1: [("POSITIVE", "POSITIVE")] * 3,
            2: [("POSITIVE", "POSITIVE"), ("NEUTRAL", "NEUTRAL"), ("POSITIVE", "POSITIVE")],
            3: [("NEGATIVE", "NEGATIVE"), ("NEGATIVE", "Negative"), ("NEGATIVE", "NEGATIVE")],
            4: [("INVALID", "ok"), ("INVALID", "ok"), ("INVALID", "ok")]}
    out = h.flip_rate(reps)
    assert out["items"] == 4 and out["repeats"] == 3
    assert out["label_flips"] == 1 and out["label_flip_ids"] == [2] and out["label_flip_rate"] == 0.25
    assert out["raw_flips"] == 2 and out["raw_flip_ids"] == [2, 3]
    assert out["invalid_responses"] == 3


def test_flip_rate_empty():
    out = h.flip_rate({})
    assert out["items"] == 0 and out["label_flip_rate"] is None and out["label_flips"] == 0


def test_hosted_record_keeps_its_session(tmp_path):
    fp = FakePost([(200, _resp())])
    r1 = h.call_hosted(MSGS, CFG, "KEY", str(tmp_path), "f", post=fp)
    assert r1["session_id"] == h.SESSION_ID and isinstance(r1["created_utc"], float)
    old = h.SESSION_ID
    h.SESSION_ID = "another-session"
    try:
        r2 = h.call_hosted(MSGS, CFG, "KEY", str(tmp_path), "f", post=FakePost([]))
    finally:
        h.SESSION_ID = old
    assert r2["from_cache"] and r2["session_id"] == old  # a cached answer keeps the session that made the call


def _raw(approach, i, rep, pred, session="s1", cache=False, lat=1.0, viol=()):
    return {"approach": approach, "filtered_index": i, "repeat": rep, "raw_response": pred, "prediction": pred,
            "session_id": session, "from_cache": cache, "latency_s": lat, "violations": list(viol)}


def test_flip_summary_from_saved_records():
    raw = [_raw("zero_shot", 1, 1, "POSITIVE"), _raw("zero_shot", 1, 3, "POSITIVE", session="s2", cache=True),
           _raw("zero_shot", 1, 2, "NEUTRAL", viol=["finish_reason:length"]),
           _raw("zero_shot", 2, 2, "NEGATIVE"), _raw("zero_shot", 2, 1, "NEGATIVE"), _raw("zero_shot", 2, 3, "NEGATIVE"),
           _raw("few_shot", 1, 1, "POSITIVE"), _raw("few_shot", 1, 2, "POSITIVE"), _raw("few_shot", 1, 3, "POSITIVE")]
    out = h.flip_summary(raw, ["zero_shot", "few_shot"])
    z = out["zero_shot"]
    assert z["items"] == 2 and z["label_flip_ids"] == [1] and z["calls"] == 6 and z["cache_hits"] == 1
    assert z["mixed_session_ids"] == [1] and z["calls_with_violations"] == 1 and z["sum_latency_s"] == 6.0
    assert out["few_shot"]["items"] == 1 and out["few_shot"]["label_flips"] == 0 and out["few_shot"]["mixed_session_ids"] == []


def test_flip_summary_rejects_duplicate_or_missing_repeats():
    with pytest.raises(AssertionError):
        h.flip_summary([_raw("zero_shot", 1, 1, "POSITIVE"), _raw("zero_shot", 1, 1, "POSITIVE")], ["zero_shot"])


def test_flip_rate_rejects_uneven_repeats():
    with pytest.raises(AssertionError):
        h.flip_rate({1: [("POSITIVE", "POSITIVE")] * 3, 2: [("POSITIVE", "POSITIVE")] * 2})
