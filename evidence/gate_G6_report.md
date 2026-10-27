```
GATE G6 REPORT (final full run)
Phase: 6 Final run      Date: 2026-10-26      Commit candidate: none (submission/ and evidence/final_run/ untracked)
Run: Colab T4 (Tesla T4, 15360 MiB), MODE final, frozen hash 8a1f06f4, build cb1a448809c5, one Run all, 21 code cells in order, 0 error outputs.
Checks (notebook outputs, submission/a4_finetune.ipynb):
- C-02..C-10, C-12, C-14, C-14b, C-15: PASS (C-01 raw-file facts printed, no PASS word)
- C-11, C-16 (x3), C-17, C-18, C-19, C-20, C-21, C-13, C-27 (x2), C-28, C-29, C-26: PASS
- C-24: all code cells executed, zero error outputs [VERIFIED: submission/a4_finetune.ipynb]
- Not yet run: C-22, C-23, C-25 (G7, G8)
Requirements: R-01, R-02, R-03, R-04, R-05, R-09, R-10, R-12, R-17, R-18, R-19, R-20, R-27, R-28, R-29, R-30, R-31, R-33 PASS per the lines above. R-11 not triggered. R-21, R-14, R-13 UNVERIFIED by me: prompts shown in S2 and INVALID 0 in both hosted files and ft_raw, but I did not review S2 output text.
Anomalies:
- Two aborted attempts. Attempt 1: SyntaxError in cell 1 (literal U+2028/2029), DEC-13, no hosted call. Attempt 2: FileNotFoundError on the Drive cache rename in S4, DEC-14. Both fixes are code changes after freeze (hash unchanged, no test result seen).
- 238 of 300 zero-shot and 2 of 300 few-shot hosted answers came from attempt 2's cache (first answer wins).
- The Secrets panel showed the class key in clear text on screen once; masked, never recorded.
- Training: Unsloth forced float32 for Gemma 3; 114 steps, 678.8 s, peak VRAM 5.15 GB, inference 141.6 s, 6.23 GB.
- I saw prediction label counts only; no metric, McNemar or confusion value read.
Decisions needing Felipe: commit including 110 MB adapter.zip in git (or ignore it); PLAN.md line 107 wording still open; run data-auditor now (PLAN 9.1 lists it at G6).
Unverified: Drive folder contents; adapter reload from the downloaded ZIP in a fresh runtime (C-25, Phase 7).
Audit: data-auditor not yet run.
Evidence: submission/ (4 files), evidence/final_run/ (9 files), LOG.md, DECISIONS.md DEC-13, DEC-14.
Next: on GO G6, data-auditor, commit, then Phase 7 (metrics-auditor, C-25 restart proof).
STOP. Awaiting "GO G6".
```
