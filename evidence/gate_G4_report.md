```
GATE G4 REPORT (freeze request)
Phase: 4 Freeze      Date: 2026-10-26      Commit candidate: none (G3 follow-up work uncommitted)
Checks:
- pytest 98 passed: evidence/phase4_pytest.log
- Notebook build 25 cells, static scan clean: tools/build_notebook.py output
- Colab dry run S0..S10, every cell DONE OK, every check PASS: evidence/phase3_dryrun_summary.md (pre-freeze section)
- Freeze hash: Colab S3 = tools/freeze.py = 8a1f06f40c4f3f273bd8149f7b4c25a9c0b20005ae5b5b435ae51be7a0e9e111: frozen_config.json, frozen_config.sha256
Frozen: prompt (system, instruction; instruction hash 2e2b8a8907c54214), hosted (Qwen3.6-35B-A3B-AWQ-4bit, temperature 0, max_tokens 8, thinking off), few-shot ids 13547, 16202, 11866, 2749, 9272, 9440, small model (unsloth/gemma-3-4b-it, 4-bit, max_seq_length 512, max_new_tokens 8, greedy, expected adapter base id, hub revisions), training (r 16, alpha 16, lr 2e-4, wd 0.01, batch 2 x accum 8, 2 epochs, adamw_8bit, seed 3407), flip rate (seed 20261029, 10 per class, 3 repeats, both prompts, 30 ids), rendered canonical prompts and parser table.
Requirements advanced: freeze protocol (PLAN 8.3) ready, PASS on approval.
Anomalies and surprises:
- S8e ran on Colab only with an empty star subset (0 of 9 dry-run titles); its non-empty path is unit-tested locally only.
- Not exercised in this run: restart-then-S6 (passed at G3, code unchanged), Drive mount, Run All with in-process pip.
Decisions needing Felipe:
- The within-class star-title table (red-team P1-5) goes beyond the approved design; keep or drop.
- PLAN.md line 107 ("Flag in the report that such titles leak the rating") states a conclusion in advance; your file, your call.
Unverified claims still open: final-run timings are estimates from the smoke.
Audit: red-team (Opus), no P0, P1-1/2/3/5 fixed, P1-4 closed by this run: DECISIONS.md "Pre-freeze red-team re-audit".
Next: on approval, set APPROVED_FREEZE_HASH, MODE "final", USE_DRIVE True in S0 (none of these are hashed), rebuild, commit, then Phase 6 final run.
STOP. Awaiting "FREEZE APPROVED 8a1f06f4".
```
