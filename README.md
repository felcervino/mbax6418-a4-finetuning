# MBAX 6418 Assignment 4: Fine-Tuning, three approaches

Compares three ways of labeling Amazon Gift Cards reviews as POSITIVE, NEUTRAL or NEGATIVE, using star ratings as the reference:

1. Hosted Qwen3.6-35B-A3B (AWQ 4-bit), zero-shot.
2. The same hosted model, few-shot (6 training examples).
3. Gemma 3 4B fine-tuned with Unsloth and QLoRA on the 900 prescribed training reviews.

All three are scored on the same 300 test reviews (first 100 per class from filtered indices 30,000 to 39,999).

## Final results (300 test reviews, no invalid answers)

| Approach | Balanced accuracy | Macro-F1 | Correct / incorrect |
|---|---|---|---|
| Hosted, zero-shot | 0.747 | 0.717 | 224 / 76 |
| Hosted, few-shot | 0.747 | 0.718 | 224 / 76 |
| Fine-tuned Gemma 3 4B | 0.810 | 0.805 | 243 / 57 |

The fine-tuned model's lead is largely in the 50 test reviews whose titles give the rating away ("Five Stars"). The report in the notebook discusses this and the limits of the comparison.

## Deliverables

The four files submitted on Canvas are in [`final_deliverables/`](final_deliverables/):

| File | Contents |
|---|---|
| `a4_finetune.ipynb` | Executed notebook: data checks, prompts, hosted runs, fine-tuning, saved-adapter inference, results, report at the bottom |
| `adapter.zip` | Only `adapter_model.safetensors` and `adapter_config.json` (stored with Git LFS) |
| `ft_test_predictions.jsonl` | The 300 fine-tuned predictions with the required fields |
| `prompt_examples.jsonl` | Three actual fine-tuned test prompts, one per reference class |

`submission/` holds the same four files as they were produced.

## Repository layout

- `src/a4_helpers.py`, `notebook_src/a4_cells.py`, `tools/build_notebook.py`: shared helpers and the notebook source; the notebook is built from these.
- `tools/verify_submission.py`, `tools/scan_secrets.py`: the final-submission verifier and the secret scanner. `tests/` holds the pytest suite.
- `evidence/`: run outputs, audits (data, metrics, red-team, submission verifier) and gate reports.
- `DECISIONS.md`, `LOG.md`, `PLAN.md`, `CLAUDE.md`: decisions, run log, plan and working rules.
- `frozen_config.json`: the configuration frozen before the final run (hash 8a1f06f4).

## Notes

- **Base model.** `adapter_config.json` names `unsloth/gemma-3-4b-it-unsloth-bnb-4bit`, Unsloth's 4-bit build of `google/gemma-3-4b-it`. The Google original is gated, and this is the model the adapter was trained on.
- **Authorship.** The report was drafted with an AI assistant at my request; the interpretation, cost and decision paragraphs follow my own answers. The notebook says so.
- **Course materials and credentials.** The assignment PDFs are kept out of this repository. The class API key is never stored in any file; the notebook reads it from Colab Secrets or the `CLASS_API_KEY` environment variable.
- **History.** The history was rewritten twice before this repository was made public (large files moved to Git LFS, and course materials and the class key removed). Commit hashes quoted in older files under `evidence/` and in `LOG.md` therefore no longer exist; the file contents are unchanged.
- **Tests.** `python -m pytest -q` runs the local test suite.
