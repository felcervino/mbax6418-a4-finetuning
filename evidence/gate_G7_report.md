```
GATE G7 REPORT (evaluation review and reload proof)
Phase: 7 Evaluation review      Date: 2026-10-27      Commit candidate: none (uncommitted: DECISIONS.md, LOG.md, evidence/ additions)
Checks:
- C-21 independent recompute: PASS, 0 differences in metrics and the 3 McNemar p-values: evidence/gate_G7_metrics_audit.md
- C-25 restart proof: PASS, 300 of 300 predictions and raw responses equal submission/ft_test_predictions.jsonl: evidence/final_run/restart_proof_ft_raw.jsonl, DECISIONS.md DEC-15
- In the proof run: C-26, C-18 (template hash 7de1c58e208eda46), C-29, C-27 (238 modules): PASS; INVALID 0, EOS ok
Requirements advanced: R-22, R-23, R-24, R-25 PASS for the numbers (independently recomputed, INVALID 0 so no INVALID column); R-23 figures not visually reviewed by me; R-30, R-31 reinforced by the proof.
Error analysis (DEC-07, first 10 ids by filtered_index per list, in the submitted notebook): fixed_by_ft 30, broken_by_ft 10, wrong_in_all 40.
Anomalies:
- Proof deviation 1: ZIP came from Drive, hash-identical to the shipped file (sha256 538010294a17...), not the literally downloaded copy (slow upload, runtime recycled).
- Proof deviation 2: I overwrote S6a in the Colab copy by mistake; S6a was run from source extracted from the submitted notebook via %run -i. Submitted notebook unaffected.
- The proof overwrote Drive a4_out/ft_raw.jsonl (not a submission file).
- Overnight runtime recycle cost about 12 hours; one earlier partial ZIP was moved but never loaded.
Decisions needing Felipe: accept DEC-15 deviations; the report prose and figures review are yours.
Unverified: figures and tables as rendered; C-22 and C-23 (G8).
Audit: metrics-auditor (Sonnet 5.5) PASS; red-team and submission-verifier at G8.
Next: on GO G7, commit, then Phase 8 (report facts tables, verify_submission and scan_secrets tools, submission-verifier, red-team at G8).
STOP. Awaiting "GO G7".
```
