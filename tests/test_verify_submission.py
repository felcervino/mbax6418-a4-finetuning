"""tools/verify_submission.py: each check passes on a good synthetic submission and fails on a targeted defect."""
import json
import os
import sys
import zipfile

import a4_helpers as h

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import verify_submission as vs  # noqa: E402

BASE_ID = "org/base-4bit"
TEST_ROWS = [{"original_row": 100 + i, "filtered_index": 30000 + i, "title": f"t{i}", "text": f"review text {i}",
              "reference_label": lab}
             for i, lab in enumerate(["POSITIVE", "NEUTRAL", "NEGATIVE", "POSITIVE", "NEUTRAL", "NEGATIVE"])]


def _pred_records(rows=TEST_ROWS, raw="POSITIVE"):
    return [{"original_row": r["original_row"], "filtered_index": r["filtered_index"], "title": r["title"],
             "text": r["text"], "reference_label": r["reference_label"], "prediction": h.parse_label(raw),
             "raw_response": raw} for r in rows]


def _write_good(tmp_path, base_id=BASE_ID):
    sub = tmp_path / "submission"
    sub.mkdir()
    with zipfile.ZipFile(sub / "adapter.zip", "w") as z:
        z.writestr("adapter_model.safetensors", b"w")
        z.writestr("adapter_config.json", json.dumps({"base_model_name_or_path": base_id}))
    h.write_predictions(str(sub / "ft_test_predictions.jsonl"), _pred_records())
    first = {}
    for r in TEST_ROWS:
        first.setdefault(r["reference_label"], r)
    with open(sub / "prompt_examples.jsonl", "w", encoding="utf-8") as f:
        for lab in h.LABELS:
            r = first[lab]
            f.write(json.dumps({"original_row": r["original_row"], "filtered_index": r["filtered_index"],
                                "reference_label": lab, "messages": h.build_prompt_for_record(r)}) + "\n")
    nb = {"cells": [{"cell_type": "code", "execution_count": 1, "source": ["x=1"], "outputs": [
        {"output_type": "stream", "name": "stdout", "text": ["ok\n"]}]},
        {"cell_type": "markdown", "source": ["# Report"]}], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}
    (sub / "a4_finetune.ipynb").write_text(json.dumps(nb), encoding="utf-8")
    return sub


def _fails(results):
    return [r["id"] for r in results if not r["pass"]]


def test_good_submission_passes(tmp_path):
    sub = _write_good(tmp_path)
    assert _fails(vs.verify(str(sub), TEST_ROWS, BASE_ID)) == []


def test_extra_or_missing_file_fails(tmp_path):
    sub = _write_good(tmp_path)
    (sub / "stray.txt").write_text("x")
    assert "S-01" in _fails(vs.verify(str(sub), TEST_ROWS, BASE_ID))
    (sub / "stray.txt").unlink()
    (sub / "prompt_examples.jsonl").unlink()
    assert "S-01" in _fails(vs.verify(str(sub), TEST_ROWS, BASE_ID))


def test_zip_with_three_files_fails(tmp_path):
    sub = _write_good(tmp_path)
    with zipfile.ZipFile(sub / "adapter.zip", "a") as z:
        z.writestr("extra.bin", b"x")
    assert "C-17" in _fails(vs.verify(str(sub), TEST_ROWS, BASE_ID))


def test_zip_base_id_mismatch_fails(tmp_path):
    sub = _write_good(tmp_path, base_id="someone/else")
    assert "C-17" in _fails(vs.verify(str(sub), TEST_ROWS, BASE_ID))


def test_predictions_row_missing_or_bad_label_fails(tmp_path):
    sub = _write_good(tmp_path)
    h.write_predictions(str(sub / "ft_test_predictions.jsonl"), _pred_records()[:-1])
    assert "C-19" in _fails(vs.verify(str(sub), TEST_ROWS, BASE_ID))
    bad = _pred_records()
    bad[0]["prediction"] = "MAYBE"
    h.write_predictions(str(sub / "ft_test_predictions.jsonl"), bad)
    assert "C-19" in _fails(vs.verify(str(sub), TEST_ROWS, BASE_ID))


def test_prompt_examples_not_first_of_class_fails(tmp_path):
    sub = _write_good(tmp_path)
    recs = [json.loads(x) for x in (sub / "prompt_examples.jsonl").read_text(encoding="utf-8").split("\n") if x]
    other = TEST_ROWS[3]  # second POSITIVE, not the first
    recs[0] = {"original_row": other["original_row"], "filtered_index": other["filtered_index"],
               "reference_label": "POSITIVE", "messages": h.build_prompt_for_record(other)}
    (sub / "prompt_examples.jsonl").write_text("\n".join(json.dumps(r) for r in recs) + "\n", encoding="utf-8")
    assert "C-20" in _fails(vs.verify(str(sub), TEST_ROWS, BASE_ID))


def test_notebook_unexecuted_cell_or_error_fails(tmp_path):
    sub = _write_good(tmp_path)
    nb = json.loads((sub / "a4_finetune.ipynb").read_text(encoding="utf-8"))
    nb["cells"][0]["execution_count"] = None
    (sub / "a4_finetune.ipynb").write_text(json.dumps(nb), encoding="utf-8")
    assert "C-24" in _fails(vs.verify(str(sub), TEST_ROWS, BASE_ID))
    nb["cells"][0]["execution_count"] = 1
    nb["cells"][0]["outputs"].append({"output_type": "error", "ename": "ValueError", "evalue": "x", "traceback": []})
    (sub / "a4_finetune.ipynb").write_text(json.dumps(nb), encoding="utf-8")
    assert "C-24" in _fails(vs.verify(str(sub), TEST_ROWS, BASE_ID))


def test_report_numbers_thousands_separators_and_notebook_outputs():
    facts = {"total_params": 4329881968}
    assert vs.report_numbers_not_in_facts("4,329,881,968 parameters", facts) == []
    assert vs.report_numbers_not_in_facts("224 correct, recall 0.35", facts) == ["224", "0.35"]
    out = "correct 224 incorrect 76 recall 0.35"
    assert vs.report_numbers_not_in_facts("224 correct, recall 0.35", facts, extra_text=out) == []
    assert vs.report_numbers_not_in_facts("recall 0.36", facts, extra_text=out) == ["0.36"]


def test_c22_uses_notebook_outputs_but_not_the_report_cell(tmp_path):
    sub = _write_good(tmp_path)
    nb = json.loads((sub / "a4_finetune.ipynb").read_text(encoding="utf-8"))
    nb["cells"][0]["outputs"][0]["text"] = ["correct 224 of 300\n"]
    nb["cells"][1]["source"] = ["The model got 224 right and 0.99 accuracy."]
    (sub / "a4_finetune.ipynb").write_text(json.dumps(nb), encoding="utf-8")
    facts = {"metrics": {"fine_tuned": {"balanced_accuracy": 0.81, "macro_f1": 0.8, "invalid": 0}}}
    res = vs.verify(str(sub), TEST_ROWS, BASE_ID, facts)
    c22 = [r for r in res if r["id"] == "C-22"][0]
    assert not c22["pass"] and "0.99" in c22["detail"] and "224" not in c22["detail"].split("[")[-1]


def test_c22_allowlist_needs_a_source_and_is_reported(tmp_path):
    sub = _write_good(tmp_path)
    nb = json.loads((sub / "a4_finetune.ipynb").read_text(encoding="utf-8"))
    nb["cells"][1]["source"] = ["accuracy 0.99 and 0.81"]
    (sub / "a4_finetune.ipynb").write_text(json.dumps(nb), encoding="utf-8")
    facts = {"metrics": {"fine_tuned": {"balanced_accuracy": 0.81, "macro_f1": 0.8, "invalid": 0}}}
    c22 = lambda allowed: [r for r in vs.verify(str(sub), TEST_ROWS, BASE_ID, facts, allowed) if r["id"] == "C-22"][0]  # noqa: E731
    assert not c22({})["pass"]
    assert not c22({"0.99": ""})["pass"]  # an allow-list entry without a source does not count
    res = c22({"0.99": "evidence/some_file.md line 3"})
    assert res["pass"] and "1 manually sourced" in res["detail"]


def test_report_numbers_must_exist_in_facts():
    facts = {"metrics": {"fine_tuned": {"balanced_accuracy": 0.81}}}
    assert vs.report_numbers_not_in_facts("accuracy was 0.81 here", facts) == []
    assert vs.report_numbers_not_in_facts("accuracy was 0.95 here", facts) == ["0.95"]
    assert vs.report_numbers_not_in_facts("no digits at all, seven topics", facts) == []
