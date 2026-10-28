# Phase 8 evidence tables for the report (facts and references only, no narrative)

Every number below was read from `evidence/final_run/report_facts.json` (RF), `evidence/final_run/train_meta.json` (TM) or `frozen_config.json` (FC) by script. Cell names are the notebook sections in `submission/a4_finetune.ipynb`. The prose is Felipe's. C-22 (`tools/verify_submission.py`) must be re-run after the prose is written.

## 0. Models, parameter counts, settings, GPU, training time (required block)
| Item | Value | Source |
|---|---|---|
| Hosted model | cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit (35B total, about 3B active) | RF hosted_model, FC hosted |
| Small model (load id) | unsloth/gemma-3-4b-it | RF small_model, FC small_model.load_id |
| Adapter base id recorded in adapter_config | unsloth/gemma-3-4b-it-unsloth-bnb-4bit | RF, DEC-12 |
| Trainable / total parameters | 29,802,496 / 4,329,881,968 | RF, TM (4-bit weights counted packed, DEC-11) |
| LoRA | r 16, alpha 16, dropout 0, modules down_proj, gate_proj, k_proj, o_proj, q_proj, up_proj, v_proj, vision layers adapted: False | RF training_settings, C-27 |
| Optimizer, learning rate, schedule | adamw_8bit, 0.0002, linear, warmup 5, weight decay 0.01 | RF training_settings |
| Batch, accumulation, epochs, seed | 2, 8, 2, 3407 | RF training_settings |
| Precision | model dtype torch.float16, fp16 False, bf16 False (Unsloth chose float32 for Gemma 3, see S5c output) | RF, notebook S5c |
| Steps, final loss | 114, 0.3283 | TM |
| Training time | 678.8 s own timer, 677.4314 s trainer | RF, TM |
| Peak VRAM training / inference | 5.15 GB / see S6c output line (final run 6.23 GB, restart proof 4.87 GB) | TM, notebook S6c, DEC-15 |
| Adapter ZIP size | 110,316,837 bytes | TM |
| Actual GPU | Tesla T4, 15360 MiB, 580.82.07; T4 tested directly: True | RF, notebook S0 |
| Generation settings | hosted {'temperature': 0, 'max_tokens': 8, 'extra_body': {'chat_template_kwargs': {'enable_thinking': False}}}; fine-tuned {'max_new_tokens': 8, 'batch_size': 1, 'do_sample': False, 'skip_special_tokens': True} | RF |
| Package versions | {"python": "3.13.16", "torch": "2.11.0+cu130", "transformers": "4.57.6", "peft": "0.21.2", "accelerate": "1.15.0", "datasets": "4.3.0", "trl": "0.22.2", "bitsandbytes": "0.50.2", "unsloth": "2026.10.9", "unsloth_zoo": "2026.10.9", "openai": "2.54.0", "requests": "2.32.4", "scikit-learn": "1.6.1", "scipy": "1.16.3", "statsmodels": "0.15.0", "pandas": "2.2.3", "numpy": "2.1.3", "matplotlib": "3.10.0", "safetensors": "0.8.0"} | RF package_versions |

## 1. Why the small model, training settings and few-shot examples
| Evidence | Where |
|---|---|
| Model candidates, token and VRAM measurements, T4 fit | DECISIONS.md D-05 / DEC-01; evidence/phase2_token_measurements.log |
| Why Phi-4-mini was dropped (only 2 module types adapted by Unsloth) and Gemma 3 4B chosen | DECISIONS.md DEC-11, DEC-11 UPDATE, D-05 re-decided |
| Training settings and loss masking | DECISIONS.md Training settings proposal, DEC-02; notebook S5c masking check |
| Few-shot ids and rule (k=6, 2 per class, train rows only) | FC fewshot_ids [13547, 16202, 11866, 2749, 9272, 9440]; DECISIONS.md D-03; evidence/phase2_fewshot_shortlist.md |
| Instruction text identical across approaches | notebook S2 C-14b; FC instruction_hash |

## 2. Best approach and specific errors
| Approach | Balanced accuracy | Macro-F1 | Correct / incorrect | INVALID |
|---|---|---|---|---|
| zero_shot | 0.7467 | 0.7173 | 224 / 76 | 0 |
| few_shot | 0.7467 | 0.7177 | 224 / 76 | 0 |
| fine_tuned | 0.8100 | 0.8049 | 243 / 57 | 0 |

Per-class precision, recall, F1 and the confusion matrices: RF metrics (all three approaches), notebook S8b and S8c, `evidence/final_run/confusion_three.png`, `confusion_best.png`.
Error lists (DEC-07, first 10 ids by filtered_index per list): notebook S8d. Totals: fixed by fine-tuning 30, broken by fine-tuning 10, wrong in all three 40. Full review text for any id: `submission/ft_test_predictions.jsonl` (fields title, text, reference_label, prediction, raw_response); hosted answers: `evidence/final_run/hosted_*_raw.jsonl`.

## 3. What the statistics support and their limits
| Pair | b | c | exact two-sided p | Source |
|---|---|---|---|---|
| few_shot vs fine_tuned | 12 | 31 | 0.005402 | RF mcnemar, independent recompute: evidence/gate_G7_metrics_audit.md |
| few_shot vs zero_shot | 6 | 6 | 1.000000 | RF mcnemar, independent recompute: evidence/gate_G7_metrics_audit.md |
| fine_tuned vs zero_shot | 34 | 15 | 0.009399 | RF mcnemar, independent recompute: evidence/gate_G7_metrics_audit.md |

No multiplicity adjustment is applied (printed in notebook S8d). b is first-named correct and second wrong; c is the reverse.
Limits stated in the plan (PLAN 4.8) with their evidence: one dataset, one small model, one few-shot set, one run per approach (DEC-15 and hosted-run policy in DECISIONS.md); hosted model not the size of the small model (RF hosted_model); star ratings are noisy proxies (assignment text).
Hosted repeatability on 30 TRAIN prompts x 3 calls, one run (RF hosted_flip_rate_train): zero-shot label flips 1 of 30 items, few-shot 0 of 30. It measures short-term repeatability, not run-to-run variation.
Title-leakage breakdown on the 300 test reviews (RF star_word_titles, notebook S8e, descriptive only): 50 star-word titles, 250 others; accuracy on star-word / other titles: few_shot 0.840 / 0.728; fine_tuned 1.000 / 0.772; zero_shot 0.780 / 0.740.

## 4. Whether the gain justifies the training time and resources
| Item | Value | Source |
|---|---|---|
| Training time | 678.8 s on a T4 | RF, TM |
| Fine-tuned inference, 300 reviews | 141.6 s (final run), 131.1 s (restart proof) | notebook S6c, DEC-15 |
| Hosted calls, 300 per approach | sum of stored per-call latencies in notebook S4 / S8d cost view; NOTE 238 of 300 zero-shot and 2 of 300 few-shot answers came from the failed attempt's cache, so S4 wall times are not comparable (DEC-14) | notebook S4, S8d, `hosted_*_raw.jsonl` from_cache field |
| Adapter size | 110,316,837 bytes | TM |
| Difference in scores | table in section 2 | RF metrics |

## 5. One issue or decision investigated with the agent
Candidates with a real investigation on record (Felipe chooses; the evaluation of the recommendation is his to write):
| Entry | What was investigated | Evidence |
|---|---|---|
| DEC-03 / DEC-05 | Qwen3.6 thinking mode and hosted nondeterminism at temperature 0 | DECISIONS.md DEC-03, DEC-05; evidence/phase0_endpoint_probe_*.jsonl, phase0_repeatability_colab.jsonl |
| DEC-10 / DEC-11 / D-05 re-decided | Unsloth tokenizer variant and LoRA targets not adapting as approved; switch to Gemma 3 4B | DECISIONS.md DEC-10, DEC-11, D-05 re-decided; evidence/phase3_template_diff.log |
| G3 and pre-freeze red-team findings | Leakage and anchoring audit, fixes made | DECISIONS.md G3 red-team findings, Pre-freeze red-team re-audit |
| DEC-13 / DEC-14 | Two infrastructure failures in the final run and their fixes after freeze | DECISIONS.md DEC-13, DEC-14 |
| DEC-15 | Restart-proof deviations (ZIP via Drive with hash match, S6a run from extracted source) | DECISIONS.md DEC-15; evidence/final_run/restart_proof_ft_raw.jsonl |

## 6. Consistency checks (C-21, C-22, C-24)
`python tools/verify_submission.py` output is saved in evidence/gate_G8_verify_submission.log; `python tools/scan_secrets.py` in evidence/gate_G8_scan_secrets.log.
