# Phase 3 dry run summary (transcribed by Claude from Colab cell outputs, 2026-10-26, Gemma 3 4B run)

Method: tools/colab_runner.py in a Colab notebook driven through Claude in Chrome (DEC-09). Notebook v4 (build/a4_finetune.ipynb at the time). MODE dryrun. Runtime: Tesla T4 15360 MiB, driver 580.82.07, python 3.13.16, torch 2.11.0+cu130, transformers 4.57.6, trl 0.22.2, unsloth 2026.10.9, unsloth_zoo 2026.10.9, bitsandbytes 0.50.2, peft 0.21.2, datasets 4.3.0. Evaluation items: 9 TRAIN rows (3 per class, not few-shot). Nothing about accuracy was read or used.

| Step | Result |
|---|---|
| S0 | PASS, class key loaded from Colab Secrets, value never printed |
| S1 | PASS, C-01..C-10 in-notebook (raw sha256 e03a258e..., zip sha256 1e827e0f...) |
| S2 | PASS, complete prompts shown for 3 approaches, C-12, C-14, C-14b, C-15 |
| S3 | frozen hash (dry, not approved) printed; changes whenever a frozen setting changes |
| S4 | 9 items zero-shot and few-shot: INVALID 0, violations 0, wall 0.9 s each |
| S5b | C-11 PASS (900 prescribed rows, 300 per class). C-16 PASS: longest training example 376 tokens, longest inference prompt 168, max_seq_length 512 |
| S5c | loaded tokenizer template equals the hub tokenizer of the load id: True. C-27 PASS: 7 projection types adapted in 34 layers, 238 modules, no vision module. Trainable 29,802,496 of 4,329,881,968 (0.69 percent). Masking PASS on 40 examples (unmasked tokens decode to LABEL plus end-of-turn). Single BOS check PASS. Unsloth switched to float32 training (fp16 and bf16 flags False): "model cannot work with float16". 10 smoke steps: own timer 108.9 s, trainer 107.2 s, avg loss 1.2265 (finite), peak VRAM 5.14 GB. Adapter files written by Unsloth: README.md, adapter_config.json, adapter_model.safetensors. ZIP: exactly the two names (C-17 namelist PASS), 110,184,609 bytes. adapter_config base_model_name_or_path = unsloth/gemma-3-4b-it-unsloth-bnb-4bit (DEC-12) |
| S6a | C-18 PASS: fresh model instance, extracted folder, template hash equal to training (7de1c58e208eda46), C-27 PASS on reload (238 modules) |
| S6b/c | example raw response 'NEGATIVE'; 9 predictions in 4.0 s, INVALID 0, all ended with EOS, peak VRAM inference 6.18 GB |
| S7 | C-13 PASS |
| S8..S10 | all cells ran; C-19, C-20 PASS; scikit-learn cross-check PASS; C-21 PASS; report facts written |

Estimates for the final run (from the smoke, [UNVERIFIED] until measured): 10.9 s per optimizer step; 2 epochs of 900 rows at effective batch 16 is 114 steps, about 21 minutes of training; 300 inference calls about 2.2 minutes.

Earlier same-day Phi-4-mini runs (superseded by D-05 re-decision) are described in LOG.md and DECISIONS.md (DEC-10, DEC-11, DEC-12).

## Re-run after the red-team fixes (notebook v5, fresh T4 runtime, transcribed 2026-10-26 18:57)
The earlier Colab runtime was recycled mid-session (new VM, empty /content); everything was re-uploaded and the whole sequence re-run: S0 to S4, install with pinned versions (73 s, all rc 0), S5b (C-28 hub revisions PASS, C-11, C-16), S5c (C-27 PASS 238 modules, masking, 10 smoke steps, ZIP with exactly two files, C-17 base id equals the frozen expected id, train_meta.json written; 199.5 s total), then Runtime > Restart session and, WITHOUT running any training cell, S0 to S4 again (cache hits), S6a (C-18 PASS template hash 7de1c58e208eda46 equal to the training run before the restart, C-29 PASS single BOS prefix, C-27 reload PASS 238 modules; 48.4 s), S6b/c (9 predictions 3.8 s, INVALID 0, all ended with EOS), S7 C-13, S8a C-19 and C-20, S8b scikit-learn cross-check, S9 C-21: all PASS. The smoke adapter, extracted folders and train_meta.json were deleted afterwards; nothing was downloaded or copied to Drive.

## Pre-freeze dry run with the two analysis cells (notebook build sha256 38e4afcd9d74..., fresh T4 runtime, transcribed 2026-10-26 19:30 to 19:44)
Method as above (Claude in Chrome, DEC-09, colab_runner.py), MODE dryrun, USE_DRIVE False. Uploaded build/a4_finetune.ipynb (sha12 38e4afcd9d74), tools/colab_runner.py, data/split_data.zip (sha12 1e827e0f1d0d); 21 code cells.
| Step | Result |
|---|---|
| S0 | PASS, GPU Tesla T4 15360 MiB driver 580.82.07, class key loaded (value never printed), config keys include flip_rate |
| S1 | C-01 raw size 12292543 sha256 e03a258e..., C-02..C-10 PASS |
| S2 | 9 evaluation items (TRAIN), DEC-05 flip sample 30 TRAIN ids starting 3863, 4004, 4350, 4917, 5374, 6239, 7518, 8054 (same as local), C-12, C-14, C-14b (2e2b8a8907c54214), C-15 PASS |
| S3 | FROZEN_HASH 8a1f06f40c4f3f273bd8149f7b4c25a9c0b20005ae5b5b435ae51be7a0e9e111, identical to tools/freeze.py locally (red-team P1-4 closed) |
| S4 | zero-shot and few-shot 9 items each: INVALID 0, violations 0, cache hits 0 |
| S4b | dry-run subset 3863, 4004, 4350 (one NEGATIVE, POSITIVE, NEUTRAL); 2 prompts x 3 items x 3 repeats = 18 calls, 18 records in hosted_flip_rate_raw.jsonl; cache folders flip_dryrun_zero_shot and flip_dryrun_few_shot; cache hits 0, mixed_session_ids [], INVALID 0, violations 0 |
| S5a | install 76.0 s, every step rc 0, same pinned versions as G3 |
| S5b | C-11, C-28, C-16 PASS (longest training example 376 tokens, inference prompt 168) |
| S5c | C-16, C-27 PASS (trainable 29,802,496 of 4,329,881,968), masking PASS on 40; 10 smoke steps own timer 107.2 s, trainer 105.8 s, final loss 1.2265, peak VRAM 5.15 GB; C-17 PASS (2 files, base id equals frozen expected id); adapter.zip 110,184,609 bytes; cell 192.5 s |
| S6a | C-18 PASS (template hash 7de1c58e208eda46), C-29 PASS, C-27 reload PASS (238 modules), 30.3 s |
| S6b/c | 9 predictions 3.9 s, INVALID 0, all ended with EOS, peak VRAM inference 6.19 GB |
| S7, S8a | C-13, C-19, C-20 PASS |
| S8b..S8d | scikit-learn cross-check PASS; all cells DONE OK |
| S8e | ran (0.0 s): star-word titles 0 of 9 dry-run items, so only the empty-subset path (n/a) was exercised on Colab; both tables printed. The non-empty path is covered only by local unit tests |
| S9 | C-21 PASS |
| S10 | report_facts.json written with frozen_hash 8a1f06f4..., hosted_flip_rate_train (rebuilt from the saved file) and star_word_titles |
Smoke artifacts deleted in the runtime afterwards (adapter.zip, adapter_extracted, adapter_train_dir, trainer_out, train_meta.json); never downloaded or copied to Drive. Accuracy numbers from these 9 TRAIN items and a 10-step adapter are plumbing only and were not used for anything. Not exercised: restart-then-S6 path (done at G3, unchanged code), Drive mount (USE_DRIVE False), Run All with in-process pip.
