"""Post-hoc, descriptive sensitivity check (not part of the notebook run, never used to tune anything).

Repeats the three exact McNemar comparisons on the test reviews WITHOUT star-word titles (and on those WITH them),
using the same star-title rule as notebook S8e (a4_helpers.STAR_TITLE). Reads saved files only.

Usage: python tools/star_title_sensitivity.py > evidence/star_title_sensitivity.txt
"""
import itertools
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import a4_helpers as h  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
ft = h.read_predictions(os.path.join(ROOT, "submission", "ft_test_predictions.jsonl"))
ref = {r["filtered_index"]: r["reference_label"] for r in ft}
title = {r["filtered_index"]: r["title"] for r in ft}
preds = {"fine_tuned": {r["filtered_index"]: r["prediction"] for r in ft}}
for name, fn in (("zero_shot", "hosted_zero_shot_raw.jsonl"), ("few_shot", "hosted_few_shot_raw.jsonl")):
    recs = h.read_predictions(os.path.join(ROOT, "evidence", "final_run", fn))
    preds[name] = {r["filtered_index"]: h.parse_label(r["raw_response"]) for r in recs}

groups = {"all 300": sorted(ref),
          "without star-word titles": sorted(i for i in ref if not h.is_star_title(title[i])),
          "star-word titles only": sorted(i for i in ref if h.is_star_title(title[i]))}
print("Exact two-sided McNemar by subgroup (b = first-named correct and second wrong, c = reverse). Descriptive only.")
for gname, ids in groups.items():
    sub_ref = {i: ref[i] for i in ids}
    mix = {c: sum(v == c for v in sub_ref.values()) for c in h.LABELS}
    print(f"\n{gname}: n={len(ids)}, reference mix {mix}")
    for a, b in itertools.combinations(("zero_shot", "few_shot", "fine_tuned"), 2):
        r = h.mcnemar_by_id(sub_ref, {i: preds[a][i] for i in ids}, {i: preds[b][i] for i in ids})
        correct = {n: sum(preds[n][i] == sub_ref[i] for i in ids) for n in (a, b)}
        print(f"  {a} vs {b}: b={r['b']} c={r['c']} p={r['p']:.4f}   correct {a} {correct[a]}, {b} {correct[b]}")
