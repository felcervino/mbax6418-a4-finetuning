import copy

import pytest

import a4_helpers as h


def _train(n_per=2):
    rows = []
    i = 1000
    for c, rt in (("POSITIVE", 5.0), ("NEUTRAL", 3.0), ("NEGATIVE", 1.0)):
        for _ in range(n_per):
            rows.append({"original_row": i, "filtered_index": i, "title": f"t{i}", "text": f"text number {i}",
                         "rating": rt, "reference_label": c})
            i += 1
    return rows


def _examples(train):
    return [{"filtered_index": r["filtered_index"],
             "messages": h.build_messages_fine_tuned(r["title"], r["text"], target=r["reference_label"])}
            for r in train]


# C-11
def test_c11_ok_and_failures():
    tr = _train()
    ex = _examples(tr)
    h.check_training_examples(ex, tr, per_class=2)
    bad = copy.deepcopy(ex)
    bad[0]["rating"] = 5.0
    with pytest.raises(AssertionError):
        h.check_training_examples(bad, tr, per_class=2)
    bad = copy.deepcopy(ex)
    bad[0]["messages"][1]["content"] += " x"
    with pytest.raises(AssertionError):
        h.check_training_examples(bad, tr, per_class=2)
    with pytest.raises(AssertionError):
        h.check_training_examples(ex[:-1], tr, per_class=2)
    dup = ex[:-1] + [ex[0]]
    with pytest.raises(AssertionError):
        h.check_training_examples(dup, tr, per_class=2)
    wrong_label = copy.deepcopy(ex)
    wrong_label[0]["messages"][-1]["content"] = "NEGATIVE"
    with pytest.raises(AssertionError):
        h.check_training_examples(wrong_label, tr, per_class=2)


# C-12
def test_c12():
    tr = _train()
    by_id = {r["filtered_index"]: r for r in tr}
    ids = [1000, 1002]
    exs = h.fewshot_examples(by_id, ids)
    assert exs[0] == ("t1000", "text number 1000", "POSITIVE")
    prompt = h.build_messages_few_shot("T", "X", exs)
    h.check_fewshot(ids, set(by_id), reserved_ids={5, 6}, prompt_messages=prompt, train_by_id=by_id)
    with pytest.raises(AssertionError):
        h.check_fewshot([1000, 999], set(by_id), {5}, prompt, by_id)      # not in train
    with pytest.raises(AssertionError):
        h.check_fewshot(ids, set(by_id), {1000}, prompt, by_id)           # in reserved
    bad = copy.deepcopy(prompt)
    bad[1]["content"] += "!"
    with pytest.raises(AssertionError):
        h.check_fewshot(ids, set(by_id), {5}, bad, by_id)                 # prompt turn differs from record


# C-13
def test_c13():
    ids = [30000, 30001, 30002]
    good = [{"filtered_index": i} for i in ids]
    h.check_one_prediction_per_id({"a": good, "b": good[::-1]}, ids)
    with pytest.raises(AssertionError):
        h.check_one_prediction_per_id({"a": good[:2]}, ids)
    with pytest.raises(AssertionError):
        h.check_one_prediction_per_id({"a": good + [{"filtered_index": 30000}]}, ids)
    with pytest.raises(AssertionError):
        h.check_one_prediction_per_id({"a": good[:2] + [{"filtered_index": 7}]}, ids)


# C-14b / C-15
def test_c14b_c15():
    zs = h.build_messages_zero_shot("T", "X")
    fs = h.build_messages_few_shot("T", "X", [("a", "b", "POSITIVE")])
    ft = h.build_messages_fine_tuned("T", "X")
    h.check_instruction_identity(zs, fs, ft)
    fs2 = copy.deepcopy(fs)
    fs2[0]["content"] += "."
    with pytest.raises(AssertionError):
        h.check_instruction_identity(zs, fs2, ft)
    h.check_prompt_inputs({"title": "T", "text": "X"}, zs)
    with pytest.raises(AssertionError):
        h.check_prompt_inputs({"title": "T", "text": "X"}, h.build_messages_zero_shot("T", "Y"))


# C-16
def test_c16():
    h.check_no_truncation([10, 20, 30], 30)
    with pytest.raises(AssertionError):
        h.check_no_truncation([10, 31], 30)


# C-19 / C-20
def _pred_records(ids):
    return [{"original_row": i, "filtered_index": i, "title": "t", "text": "x", "reference_label": "POSITIVE",
             "prediction": "POSITIVE", "raw_response": "POSITIVE"} for i in ids]


def test_c19():
    ids = [1, 2, 3]
    h.check_predictions_records(_pred_records(ids), ids)
    with pytest.raises(AssertionError):
        h.check_predictions_records(_pred_records(ids[:2]), ids)
    bad = _pred_records(ids)
    bad[0]["prediction"] = "MAYBE"
    with pytest.raises(AssertionError):
        h.check_predictions_records(bad, ids)
    bad = _pred_records(ids)
    bad[0] = {k: bad[0][k] for k in reversed(list(bad[0]))}
    with pytest.raises(AssertionError):
        h.check_predictions_records(bad, ids)  # field order


def test_c20():
    recs = []
    for i, c in enumerate(h.LABELS):
        msgs = h.build_messages_fine_tuned("t%d" % i, "text %d" % i)
        recs.append({"original_row": i, "filtered_index": i, "reference_label": c, "messages": msgs})
    expected = {i: r["messages"] for i, r in enumerate(recs)}
    h.check_prompt_examples(recs, expected)
    bad = copy.deepcopy(recs)
    bad[1]["reference_label"] = "POSITIVE"
    with pytest.raises(AssertionError):
        h.check_prompt_examples(bad, expected)  # not one per class
    bad = copy.deepcopy(recs)
    bad[0]["messages"][1]["content"] += " NEGATIVE"
    with pytest.raises(AssertionError):
        h.check_prompt_examples(bad, expected)  # differs from rebuilt
    bad = copy.deepcopy(recs)
    bad[0]["messages"].append({"role": "assistant", "content": "POSITIVE"})
    bad2 = {0: bad[0]["messages"], 1: recs[1]["messages"], 2: recs[2]["messages"]}
    with pytest.raises(AssertionError):
        h.check_prompt_examples(bad, bad2)  # label inside messages


# C-07 static scan
def test_static_scan():
    ok = ["x = 1\nprint(x)", "def f(): return train_rows"]
    h.scan_forbidden_tokens(ok, [r"\bval\b", "SEALED"])
    with pytest.raises(AssertionError):
        h.scan_forbidden_tokens(["a = splits['val']"], [r"\bval\b"])
    with pytest.raises(AssertionError):
        h.scan_forbidden_tokens(["print(SEALED_LABELS)"], ["SEALED"])
    h.scan_forbidden_tokens(["evaluate = 1; interval = 2"], [r"\bval\b"])


def test_config_hash_of_frozen():
    cfg = {"hosted": {"model": "m"}, "fewshot_ids": [1, 2], "volatile_note": "x"}
    a = h.frozen_hash(cfg, keys=["hosted", "fewshot_ids"])
    b = h.frozen_hash(dict(cfg, volatile_note="y"), keys=["hosted", "fewshot_ids"])
    assert a == b
    assert a != h.frozen_hash(dict(cfg, fewshot_ids=[2, 1]), keys=["hosted", "fewshot_ids"])
