# Pre-G8 submission-verifier report (2026-10-27, Sonnet 5.5 subagent, read-only), saved as received in condensed form
Verdict: no blocking findings. verify_submission (S-01, C-17, C-19, C-20, C-24, C-21f, C-22) and scan_secrets (C-23, 0 hits) pass; exact class-key search skipped, CLASS_API_KEY not set.
- Notebook: 25 cells, 21 code cells executed in order (counts 1 to 21), 0 error outputs; prints MODE final; no dry-run text in outputs; no key-like strings in outputs (long tokens are dashes and hub revision hashes). Report cell is still the placeholder.
- ZIP: exactly adapter_model.safetensors and adapter_config.json; base id unsloth/gemma-3-4b-it-unsloth-bnb-4bit.
- Predictions: 300 rows, unique ids, field order per PLAN 4.7, 100 reference rows per class, every prediction appears in its raw_response, raw responses are bare one-word labels.
- prompt_examples: 3 rows, ids 30000 POSITIVE, 30005 NEGATIVE, 30008 NEUTRAL, first of each class; title and text match the prediction record once; label not in messages.
- Metrics recomputed from the file equal the notebook (balanced accuracy 0.8100, macro-F1 0.8049, 243 correct / 57 incorrect).
Items the scripts cannot catch (auditor's list) and my check of each:
1. S0 cell comment says the hub revisions came from the dry run: true by design, C-28 PASS in the final run means the revisions were unchanged (notebook_src/a4_cells.py line 34).
2. S0 lists trl, bitsandbytes, unsloth as "not installed": S0 runs before the install cell; the recorded versions after the install are in report_facts.json and train_meta.json (unsloth 2026.10.9, trl 0.22.2, bitsandbytes 0.50.2, torch 2.11.0+cu130, transformers 4.57.6, peft 0.21.2).
3. Fine-tuned accuracy on the 50 star-word titles is 1.00 (50 of 50) versus 0.772 on the other 250 [VERIFIED: report_facts.json star_word_titles]; a point for the report to address, wording is Felipe's.
4. Report cell not yet checked against saved outputs: pending the prose (C-22).
