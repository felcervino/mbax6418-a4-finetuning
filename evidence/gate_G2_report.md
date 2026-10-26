GATE G2 REPORT
Phase: 2 Decisions      Date: 2026-10-26      Commit candidate: none yet

Checks:
- Every D-xx answered and logged: PASS for D-01, D-02, D-03, D-04, D-05, DEC-02, DEC-05, training settings (DECISIONS.md); D-06 to D-09 and DEC-07 were approved at G0
- Few-shot ids: all six in train, none in test (checked at approval; no saved file)
- Token limits and template facts measured: evidence/phase2_token_measurements.log (train rows only)
- Nothing frozen, trained or run on Colab in this phase

Decisions made:
- Default prompt, no NEUTRAL guidance; max_tokens 8 hosted and max_new_tokens 8 small
- Phi-4-mini-instruct loaded by original microsoft id (fallback Gemma 3 4B); assistant-only loss; r16/alpha16, lr 2e-4, batch 2 x accum 8, 2 epochs, one run
- DEC-05: single reported run plus a separate 30 x 3 train flip-rate measurement
- Few-shot k=6: 13547, 16202, 11866, 2749, 9272, 9440 in that order (RNG 20261028)

Anomalies and surprises:
1. Unsloth docs were read through a summarizer and have no dates. They say nothing on Phi-4-mini on a T4, the optimizer, or T4 precision flags, and they disagree on gradient accumulation (4 vs 8). Not guessed.
2. Whether loading by the microsoft id records that id in adapter_config is UNVERIFIED until the Phase 3 dry run.
3. Response markers for Phi-4-mini (<|user|>, <|assistant|>) come from the rendered template, not the docs. Must be proven by decoding unmasked labels.
4. Two few-shot examples have noisy labels (13547 rated 4 but mixed, 9272 rated 1 but neutral-sounding).
5. 98 of 900 train titles are star-word titles (leakage); 57 texts contain "<br />".

Decisions needing Felipe: none open.
Unverified claims still open: Unsloth settings above; Phi-4-mini T4 fit and speed; base id in adapter_config.
Felipe read the 20 training examples (evidence/phase2_training_examples_20.md): NOT CONFIRMED yet. The PDF asks for this; please confirm or flag issues.
Audit: none scheduled for G2.
Next: after GO G2, commit, then Phase 3 (notebook build and dry run, Colab MCP, fetch Unsloth notebook settings, red-team at G3 on Opus 5.5).
STOP. Awaiting "GO G2".
