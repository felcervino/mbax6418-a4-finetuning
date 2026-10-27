# G7 metrics-auditor report (2026-10-26, Sonnet 5.5 subagent, read-only)
Auditor's own code: /tmp/a/audit.py (outside the repo, a4_helpers not used). Saved as received, only layout condensed. Recomputed from evidence/final_run/hosted_zero_shot_raw.jsonl, hosted_few_shot_raw.jsonl and submission/ft_test_predictions.jsonl.

Result: no differences found. Every number matches evidence/final_run/report_facts.json (metrics and mcnemar): exact for balanced accuracy and macro-F1, full float precision for McNemar p.
- The 300 ids align by filtered_index in all three files; reference labels in submission/ft_test_predictions.jsonl equal the test split in data/split_data.zip.
- Auditor's parse of raw_response (strip, upper, exact match) equals the stored prediction in all 300 rows of each file: 0 mismatches.
- INVALID is 0 for all three approaches, so no INVALID column.
- Confusion rows are reference, columns POS, NEU, NEG, INVALID.

| Approach | BA | macro-F1 | Correct / incorrect | P / R / F1 POS | P / R / F1 NEU | P / R / F1 NEG | Matrix (POS; NEU; NEG) |
|---|---|---|---|---|---|---|---|
| zero_shot | 0.7467 | 0.7173 | 224 / 76 | .844 / .92 / .880 | .796 / .35 / .486 | .660 / .97 / .785 | [92,8,0,0]; [15,35,50,0]; [2,1,97,0] |
| few_shot | 0.7467 | 0.7177 | 224 / 76 | .852 / .92 / .885 | .796 / .35 / .486 | .655 / .97 / .782 | [92,8,0,0]; [14,35,51,0]; [2,1,97,0] |
| fine_tuned | 0.8100 | 0.8049 | 243 / 57 | .853 / .93 / .890 | .778 / .63 / .696 | .791 / .87 / .829 | [93,7,0,0]; [14,63,23,0]; [2,11,87,0] |

Exact two-sided McNemar (scipy binomtest); b = first-named correct and second wrong, c = reverse (same as the notebook):
| Pair | b | c | p |
|---|---|---|---|
| few_shot vs fine_tuned | 12 | 31 | 0.005402 |
| few_shot vs zero_shot | 6 | 6 | 1.0 |
| fine_tuned vs zero_shot | 34 | 15 | 0.009399 |

Notes from the auditor: it did not recompute the statsmodels p itself, it compared its scipy p with the stored value (they agree). scipy was not installed in its environment, so it ran pip install scipy there (not in the repo; no repo file edited).
