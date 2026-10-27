GATE G3 REPORT
Phase: 3 Notebook build and dry run      Date: 2026-10-26      Commit candidate: none yet (needs Felipe's OK)

Checks:
- Tests: 83 passed (T-01..T-08, checks, hosted layer, prefix, notebook build, real-data). evidence/gate_G1_pytest.log is from G1; rerun output in LOG.md
- Notebook builds (23 cells), every cell compiles, static scan clean (build/a4_finetune.ipynb)
- Colab dry run, Gemma 3 4B, T4: S0..S10 PASS incl. C-11, C-13, C-16..C-21, C-27, C-28, C-29, restart-then-reload (evidence/phase3_dryrun_summary.md, transcribed)
- Memory fit: smoke peak 5.14 GB train, 6.18 GB inference (T4 15 GB); float32 training; about 10.9 s/step => about 21 min for the real run [UNVERIFIED until measured]
- Red-team (Opus): P0 1, P1 7, P2 7. Code fixes done for P1 items 2 to 8; P0 and the hosted-run policy need your decision

Requirements advanced: R-03 (fits T4), R-09, R-12, R-18..R-20, R-30, R-31 now demonstrated in a dry run; R-27 pending DEC-12.

Anomalies and surprises:
1. Colab MCP unusable (DEC-09); Chrome-driven instead. Colab runtime was recycled once; artifacts must go to Drive in the real run.
2. Phi-4-mini abandoned after DEC-10..12 (Unsloth cannot adapt fused projections); Gemma 3 4B chosen (D-05 re-decided).
3. Gemma 3 trains in float32 on T4 (Unsloth declines fp16).
4. adapter_config names unsloth/gemma-3-4b-it-unsloth-bnb-4bit; original google/gemma-3-4b-it is gated.
5. Dry-run frozen hash changes with any frozen setting; no hash approved yet.

Decisions answered 2026-10-26: DEC-12 (a) keep the id Unsloth writes; hosted calls only in the final run (cache on Drive).
Unverified: full-run time and VRAM with all 900 rows; Run All with in-process pip (dry run used the harness); title-leakage analysis and DEC-05 flip-rate cells not built yet.
Audit: red-team Opus 5.5, verdict "do not freeze" until DEC-12; findings recorded in DECISIONS.md (not saved verbatim).
Next: after GO G3 and DEC-12, build the two approved analysis cells, re-run red-team on the changes if you want, then Phase 4 freeze.
STOP. Awaiting "GO G3".
