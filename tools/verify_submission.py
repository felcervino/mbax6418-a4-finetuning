"""Phase 8 submission verifier: file set, adapter ZIP, predictions file, prompt examples, notebook execution state.

Usage: python tools/verify_submission.py [submission_dir] [report_facts.json]
Prints one PASS/FAIL line per check and exits 1 on any failure. Checks: S-01 file set, C-17 ZIP, C-19 predictions,
C-20 prompt examples, C-24 notebook executed with zero error outputs, C-21f fine-tuned metrics vs report_facts,
C-22 report numbers vs report_facts (scripted extraction).
"""
import json
import os
import re
import sys
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import a4_helpers as h  # noqa: E402

EXPECTED_FILES = {"a4_finetune.ipynb", "adapter.zip", "ft_test_predictions.jsonl", "prompt_examples.jsonl"}
NUM = re.compile(r"(?<![\w.])\d+(?:\.\d+)?")


def _flatten_numbers(obj, out):
    if isinstance(obj, bool):
        return
    if isinstance(obj, (int, float)):
        out.append(float(obj))
    elif isinstance(obj, dict):
        for v in obj.values():
            _flatten_numbers(v, out)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            _flatten_numbers(v, out)
    elif isinstance(obj, str):
        for m in NUM.findall(obj):
            out.append(float(m))


def _plain_numbers(text):
    """Numbers in free text, with thousands separators removed first (4,329,881,968 is one number)."""
    return NUM.findall(re.sub(r"(?<=\d),(?=\d{3}(?!\d))", "", text))


def report_numbers_not_in_facts(text, facts, extra_text=""):
    """C-22: numbers written in the report text that match no number in the saved facts or in the saved outputs
    (extra_text, e.g. the notebook's cell outputs). Rounding and percent forms are allowed."""
    known = []
    _flatten_numbers(facts, known)
    known += [float(t) for t in _plain_numbers(extra_text)]
    missing = []
    for tok in _plain_numbers(text):
        val = float(tok)
        dec = len(tok.split(".")[1]) if "." in tok else 0
        tol = 0.5 * 10 ** (-dec) + 1e-12
        if "." not in tok and val <= 10:
            continue  # counting words and digits such as 3 approaches or 7 topics
        ok = any(abs(k - val) <= tol or abs(k * 100 - val) <= tol for k in known)
        if not ok:
            missing.append(tok)
    return missing


def _run(results, cid, fn):
    try:
        detail = fn()
        results.append({"id": cid, "pass": True, "detail": detail or ""})
    except Exception as e:  # noqa: BLE001 every failure must be reported, not raised
        results.append({"id": cid, "pass": False, "detail": f"{type(e).__name__}: {e}"[:300]})


def _read_jsonl(path):
    with open(path, "r", encoding="utf-8", newline="") as f:
        return [json.loads(x) for x in f.read().split("\n") if x.strip()]


def verify(sub_dir, test_rows, expected_base_id, facts=None, allowed=None):
    results = []
    p = lambda n: os.path.join(sub_dir, n)  # noqa: E731

    def s01():
        names = set(os.listdir(sub_dir))
        assert names == EXPECTED_FILES, f"extra {sorted(names - EXPECTED_FILES)} missing {sorted(EXPECTED_FILES - names)}"
        return "exactly the four files"

    def c17():
        names = h.verify_adapter_zip(p("adapter.zip"))
        with zipfile.ZipFile(p("adapter.zip")) as z:
            assert z.testzip() is None, "corrupt ZIP member"
            cfg = json.loads(z.read("adapter_config.json"))
        got = cfg.get("base_model_name_or_path")
        assert got == expected_base_id, f"base id {got!r} != {expected_base_id!r}"
        return f"names {names}, base id {got}"

    def c19():
        recs = h.read_predictions(p("ft_test_predictions.jsonl"))
        h.check_predictions_records(recs, [r["filtered_index"] for r in test_rows])
        by = {r["filtered_index"]: r for r in test_rows}
        for r in recs:
            t = by[r["filtered_index"]]
            for k in ("original_row", "title", "text", "reference_label"):
                assert r[k] == t[k], f"{k} differs from the test split for id {r['filtered_index']}"
        return f"{len(recs)} rows, fields {h.PREDICTION_FIELDS}"

    def c20():
        recs = _read_jsonl(p("prompt_examples.jsonl"))
        by = {r["filtered_index"]: r for r in test_rows}
        expected = {r["filtered_index"]: h.build_prompt_for_record(by[r["filtered_index"]]) for r in recs}
        h.check_prompt_examples(recs, expected)
        for r in recs:
            assert list(r.keys()) == ["original_row", "filtered_index", "reference_label", "messages"], list(r.keys())
            first = min(t["filtered_index"] for t in test_rows if t["reference_label"] == r["reference_label"])
            assert r["filtered_index"] == first, f"id {r['filtered_index']} is not the first {r['reference_label']} test review"
            assert by[r["filtered_index"]]["reference_label"] == r["reference_label"]
        return "ids " + ", ".join(str(r["filtered_index"]) for r in recs)

    def c24():
        with open(p("a4_finetune.ipynb"), encoding="utf-8") as f:
            nb = json.load(f)
        code = [c for c in nb["cells"] if c["cell_type"] == "code"]
        counts = [c.get("execution_count") for c in code]
        assert all(isinstance(x, int) for x in counts), f"unexecuted code cells: {counts.count(None)}"
        assert counts == sorted(counts) and len(set(counts)) == len(counts), "execution counts not strictly increasing"
        errs = [o for c in code for o in c.get("outputs", []) if o.get("output_type") == "error"]
        assert not errs, f"{len(errs)} error outputs"
        return f"{len(code)} code cells executed in order, 0 error outputs"

    _run(results, "S-01", s01)
    _run(results, "C-17", c17)
    _run(results, "C-19", c19)
    _run(results, "C-20", c20)
    _run(results, "C-24", c24)

    if facts is not None:
        def c21f():
            recs = h.read_predictions(p("ft_test_predictions.jsonl"))
            m = h.compute_metrics([r["reference_label"] for r in recs], [r["prediction"] for r in recs])
            want = facts["metrics"]["fine_tuned"]
            for k in ("balanced_accuracy", "macro_f1", "invalid"):
                assert abs(m[k] - want[k]) < 1e-12, f"{k}: file {m[k]} vs facts {want[k]}"
            return "fine-tuned metrics from the file equal report_facts.json"

        def c22():
            with open(p("a4_finetune.ipynb"), encoding="utf-8") as f:
                nb = json.load(f)
            md = [c for c in nb["cells"] if c["cell_type"] == "markdown"]
            report = "".join(md[-1]["source"])
            outs = []
            for c in nb["cells"]:
                if c["cell_type"] != "code":
                    continue
                for o in c.get("outputs", []):
                    outs.append("".join(o.get("text", [])) if o.get("output_type") == "stream"
                                else "".join(o.get("data", {}).get("text/plain", [])))
            bad = report_numbers_not_in_facts(report, facts, chr(10).join(outs))
            sourced = {k for k, v in (allowed or {}).items() if str(v).strip()}
            manual = [n for n in bad if n in sourced]
            bad = [n for n in bad if n not in sourced]
            assert not bad, f"report numbers not in saved facts, notebook outputs or the sourced allow-list: {bad}"
            return (f"report cell checked, {len(_plain_numbers(report))} numbers found, none unmatched; "
                    f"{len(set(manual))} manually sourced ({', '.join(sorted(set(manual)))})")

        _run(results, "C-21f", c21f)
        _run(results, "C-22", c22)
    return results


def main():
    root = os.path.join(os.path.dirname(__file__), "..")
    sub_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(root, "submission")
    facts_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(root, "evidence", "final_run", "report_facts.json")
    test_rows = h.read_zip_splits(os.path.join(root, "data", "split_data.zip"))["test"]
    with open(os.path.join(root, "frozen_config.json"), encoding="utf-8") as f:
        expected_base = json.load(f)["small_model"]["expected_adapter_base_id"]
    facts = None
    if os.path.exists(facts_path):
        with open(facts_path, encoding="utf-8") as f:
            facts = json.load(f)
    allow_path = os.path.join(root, "evidence", "report_number_sources.json")
    allowed = json.load(open(allow_path, encoding="utf-8")) if os.path.exists(allow_path) else {}
    results = verify(sub_dir, test_rows, expected_base, facts, allowed)
    for r in results:
        print(f"{r['id']}: {'PASS' if r['pass'] else 'FAIL'} | {r['detail']}")
    if facts is None:
        print("C-21f, C-22: skipped, no report_facts.json")
    sys.exit(0 if all(r["pass"] for r in results) else 1)


if __name__ == "__main__":
    main()
