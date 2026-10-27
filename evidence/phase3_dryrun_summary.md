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
