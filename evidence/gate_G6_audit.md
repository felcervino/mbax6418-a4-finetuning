# G6 data-auditor report (2026-10-26, Sonnet 5.5 subagent, read-only)
Auditor's own code: /tmp/aud/a.py (outside the repo, a4_helpers not used). The text below is the subagent's report, saved as received.

- C-01 PASS: 152,410 lines, 151,240 survivors, no bad ratings or non-string text; sha256 prefix e03a258ebd7b, 12,292,543 bytes.
- C-02 PASS: id sets and (filtered_index, original_row) pairs match data/split_data.zip for train, val, test; title, text, rating, label match, 0 mismatches.
- C-03 PASS. C-04 PASS (observed train 1010-19975, val 20000-25135, test 30000-35859). C-05 PASS (Random(43) order identical). C-06 PASS. C-07 PASS, val side only (static scan of code after S1 not run by the auditor). C-08 PASS (900/300/300, balanced). C-09 PASS. C-10 PASS (0 overlap).
- Final run files vs rebuild: ft_raw.jsonl, hosted_zero_shot_raw.jsonl, hosted_few_shot_raw.jsonl and submission/ft_test_predictions.jsonl each cover exactly the 300 test ids; original_row, title, text match, 0 mismatches. reference_label matches the rebuilt test label for all 300 ids.
- prompt_examples.jsonl: 3 rows, ids 30000 (POSITIVE), 30008 (NEUTRAL), 30005 (NEGATIVE), the first test review of each class; keys only filtered_index, original_row, reference_label, messages. The auditor did not inspect the assistant messages.
- fewshot_ids 13547, 16202, 11866, 2749, 9272, 9440: all train ids, none val or test; 2 POSITIVE, 2 NEUTRAL, 2 NEGATIVE.
- s1_data_checks.json agrees with the auditor's C-02 to C-10 results. Gaps: it has no C-01 entry (the raw sha256 and line count are in the notebook output instead), and its C-07 entry is C-07a (val side only).
- No accuracy or F1 computed, no review text printed.
