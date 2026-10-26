# PLAN.md: MBAX 6418 Assignment 4 (Fine-Tuning: Compare Three Approaches)

Owner: Felipe (individual submission). Executor: Claude Code. Kickoff: Mon 2026-10-26.
Deadline: ASSUMED end of week (Fri 2026-10-30). UNCONFIRMED, see section 12.
Source of truth for requirements: docs/assignment4.pdf. If this plan and the PDF disagree, the PDF wins and you tell Felipe.

## 0. How to read this file (token rules)

- Session start: read CLAUDE.md, `tail -n 40 LOG.md`, sections 1 and 2, and ONLY the active phase in section 7.
  Find sections with `grep -n '^## ' PLAN.md`, read with `sed -n 'A,Bp' PLAN.md`.
- Never re-read the full assignment PDF. Use requirement IDs (section 3). For a dispute, `grep -n -i "<phrase>" docs/assignment4.txt`.
- Appendices A and B are read once, in Phase 0, to create files. Never again.
- Every factual claim in chat is tagged `[VERIFIED: path]` or `[UNVERIFIED]`. Untagged claims are treated as unverified.
- Command output is capped (`| head -n 40`, `| tail -n 30`). Never print datasets, full notebooks, or full training logs.

## 1. Mission

Build ONE Google Colab notebook that classifies Amazon Gift Cards reviews as POSITIVE, NEUTRAL or NEGATIVE with three approaches on the same 300 test reviews:
(1) zero-shot and (2) few-shot on the hosted model, (3) a small open-weight model fine-tuned with Unsloth + QLoRA. Then evaluate, explain, and ship four files.

Grading focus (from the PDF): the fine-tuned model's data integrity, evaluation, reproducible inference, the four submission files, and Felipe's decisions and interpretation.
Fine-tuning does not need to win. Significance is not required. Nothing in this plan may pressure results toward an expected story.

Non-goals: dashboards, hyperparameter search, use of the validation set, merging the adapter, extra approaches, extra models.

Done means: every R-xx in section 3 is PASS with evidence, Gate G8 passed, Felipe downloaded the four files and submits on Canvas himself.

## 2. Standing rules

1. Assume nothing. If a fact, number, version, model id or API is not in the PDF, the class materials, or a file you just read, look it up (fetch docs, run a command) or ask Felipe. Never state package versions, model sizes, VRAM numbers or hyperparameter defaults from memory.
2. Ask ALL questions in one batch before acting, per phase. No partial work on unanswered questions.
3. Never trust the agent (yourself included). Every check is code that raises on failure. A failed check stops the affected step.
4. Gates: at each gate output the Gate Report (Appendix C), then STOP. Proceed only on the literal reply `GO Gx` from Felipe.
5. The validation set is reserved. No code path after the data-verification step may read it. Test labels are read only by the scoring step.
6. Test freeze (section 8.3). After `FREEZE APPROVED`, prompts, few-shot ids, model ids and generation settings do not change. No test result may influence any model or prompt.
7. Credentials: the class API key is read from Colab Secrets or an environment variable, never written into any file, notebook source, or output. Never commit secrets.
8. Git: private repo, commit at each gate. Show `git status --short` and the commit message before committing. Never push without Felipe's go-ahead. Never submit to Canvas.
9. No em dashes in any text you write for Felipe, including the notebook report, commit messages, and chat.
10. The notebook report prose is Felipe's. You draft evidence and facts only (section 4.8). Never write conclusions he has not seen the numbers for.
11. Keep one decision log (DECISIONS.md). Felipe must be able to point to a real investigation for the report item "one important issue or decision investigated with your agent".
12. Be brutal: report every anomaly, even ones that look harmless. Do not smooth over a failing check, a mismatch, or an odd number. Do not retrofit explanations.

## 3. Requirement traceability

ID | Requirement (short) | Evidence | Gate
---|---|---|---
R-01 | One Colab notebook, runs top to bottom, no errors | C-24, executed run log | G6
R-02 | Zero-shot and few-shot on hosted model cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit via class endpoint | S4 outputs, raw responses | G5
R-03 | Small open-weight model, Unsloth + QLoRA, about 2 to 5B to start, fits T4 16 GB | DEC-01, VRAM peaks | G2, G6
R-04 | Labels: 4-5 POSITIVE, 3 NEUTRAL, 1-2 NEGATIVE | C-03, T-02 | G1
R-05 | Splits rebuilt from raw per spec (original_row from 1, skip rules, filtered_index from 0) | C-01, C-02 | G1
R-06 | Train: idx 1000-19999, 300/class, one Random(43), class order POS, NEU, NEG, then shuffle | C-04, C-05 | G1
R-07 | Val: idx 20000-29999, first 100/class, reserved, unused | C-07 | G1
R-08 | Test: idx 30000-39999, first 100/class | C-06 | G1
R-09 | Pre-training checks incl. actual prepared records and few-shot subset of train | C-08 to C-12 | G3, G6
R-10 | Pre-scoring: exactly one prediction per test ID per approach, align by ID | C-13 | G6
R-11 | Adapter trained on bad or unverifiable rows is retrained from original base, fresh adapter | section 8.5 | G6
R-12 | Inputs are title and text only; no rating field or label | C-14, C-15 | G3
R-13 | No test reviews in training or few-shot; no test results used to adjust anything | C-12, C-26 | G4
R-14 | Invalid responses recorded, never dropped or guessed | C-13, T-03 | G6
R-15 | No credentials in public copies | C-23 | G8
R-16 | Completed tests distinguished from unverified claims | tagging rule, report | G8
R-17 | Actual GPU and whether T4 was tested directly are reported | S0 output, report | G6
R-18 | Same task instructions across approaches; exactly one label requested | C-14b | G3
R-19 | FT uses same prompt structure and review formatting in training and inference; titles as provided | C-11, C-18 | G6
R-20 | Temperature 0 or greedy, small output-token limit, thinking disabled, recorded per approach | CONFIG, DEC-03 | G3
R-21 | Complete prompts shown for the same test review incl. all few-shot examples; results section separate from prediction code | S2, S8 | G6
R-22 | Balanced accuracy, macro-F1, per-class P/R/F1, correct and incorrect counts per approach | S8, C-21 | G7
R-23 | Three row-normalized confusion matrices side by side, plus enlarged one for best macro-F1 | S8 | G7
R-24 | Exact pairwise McNemar for all three pairs, statistics package, p-values explained | S8 | G7
R-25 | INVALID normalization, counted incorrect, INVALID column if any, averages over 3 classes only | T-03, S8 | G7
R-26 | Report items (7): model, settings, few-shot rationale; best approach with errors; stats limits; cost vs gain; decision investigated; names/params/GPU/time | S10 | G8
R-27 | Adapter ZIP has only adapter_model.safetensors and adapter_config.json; config identifies base model | C-17 | G8
R-28 | Predictions file: 300 rows, exact fields | C-19 | G8
R-29 | prompt_examples.jsonl: 3 rows, one per class, match predictions | C-20 | G8
R-30 | Labeled runnable saved-adapter inference example, same procedure as the 300 predictions, versions and settings recorded | S6, C-18 | G6
R-31 | Adapter extracted from the ZIP to a separate folder, loaded in a fresh model instance; final files generated from it; FT scores computed from the file | C-18, C-21 | G6
R-32 | All four files and report agree; downloaded before leaving Colab | verify_submission.py, C-22 | G8
R-33 | Model and tokenizer ids, tested package versions recorded | S0, S6 | G6

## 4. Technical specification

### 4.1 Data (fixed, do not change)

- Source: Amazon Reviews '23 Gift Cards `.jsonl.gz` (URL in the PDF). `data/split_data.zip` (train 900, val 300, test 300) is a CROSS-CHECK only, never the source.
- Builder (`build_splits`, pure Python, in `src/a4_helpers.py`):
  1. Read the gz line by line. `original_row` = 1-based physical line number (blank lines still count).
  2. Skip lines where `line.strip()` is empty. Parse JSON. `text = rec.get("text")`, missing/None becomes `""`. Skip if `len(text.strip()) < 3`. Title is not part of the filter.
  3. `filtered_index` = 0-based counter over survivors, in file order.
  4. Label from `rating`: >=4 POSITIVE, ==3 NEUTRAL, <=2 NEGATIVE. Report any rating outside {1..5} or any non-string text instead of guessing.
  5. Train pool per class = survivors with index in [1000, 19999] in file order. `rng = random.Random(43)` created ONCE. For POSITIVE, NEUTRAL, NEGATIVE in that order: `rng.sample(pool, 300)`. Concatenate, then `rng.shuffle(combined)` with the same `rng`. No other use of `rng` anywhere.
  6. Val: index [20000, 29999], first 100 per class in file order. Test: index [30000, 39999], first 100 per class in file order.
- Verified by Claude (chat) on the zip alone: counts 900/300/300, class balance, unique and disjoint ids, ratings consistent with labels, no empty titles, no texts under 3 characters. Val and test files are NOT stored in filtered_index order: align by ID, never by position. Not yet verified: that the builder reproduces the zip from the raw file. That is G1.
- Fields kept: original_row, filtered_index, title, text, rating, reference_label (rating and label stay in the records but are NEVER passed to a prompt builder).

### 4.2 Prompts (decision slots marked D-xx need Felipe's approval)

- Default structure comes from Week 9 slide "Training Examples", adapted to three labels:
  - system: `You are an expert product review analyst. Determine the sentiment each Amazon review expresses.`
  - user: `Classify the sentiment of the review below as exactly one of: POSITIVE, NEUTRAL, NEGATIVE. Reply with exactly one word, no explanation.` + blank line + `Review title: {title}` + newline + `Review text: {text}`
  - assistant (training target and expected answer): the label only.
- D-01: Phase 0 reads Felipe's Assignment 1 repo prompt for continuity. Propose reconciling it with the default above. Any wording change is made once, before the freeze, and applied identically to all three approaches.
- D-02: whether to add NEUTRAL guidance (for example "3-star reviews"). Default: no extra definitions. If added, identical in all three.
- Zero-shot: system + user(target).
- Few-shot: same system, then k pairs of user(example)/assistant(label), then user(target). Instruction text is byte-identical to zero-shot (C-14b).
- Fine-tuned: same system + user(target) structure as zero-shot, assistant = label. No examples at inference.
- Title and text are inserted exactly as provided (no cleaning, no case change), including titles such as "Five Stars". Flag in the report that such titles leak the rating for all three approaches.
- D-03 few-shot: k and selection. Proposal flow: a script drafts a candidate shortlist from the 900 train rows with a SEPARATE RNG (constant recorded, never Random(43)); Felipe approves the final set after reading each example; includes at least one hard NEUTRAL; selected by rule, not by test behavior. k is a multiple of 3 so classes are balanced.
- Prompt builders take `(title, text)` only. Unit test (C-14) proves output is identical when rating and label are changed.

### 4.3 Hosted model (zero-shot and few-shot)

- OpenAI-compatible client, base URL `http://dobolyi.com:9001/v1`, model `cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit` (35B total, about 3B active per the PDF). Key from secret/env only.
- Settings recorded in CONFIG: temperature 0, max_tokens N (D-04, see below), thinking disabled, stop/seed if used.
- DEC-03 (must be investigated, not assumed): how to disable thinking on this endpoint (likely a chat-template flag passed via `extra_body`). Test on train rows. Evidence required: response contains no reasoning content and `content` is the bare label. If thinking is not truly off, a small max_tokens yields EMPTY content and mass INVALID. That would be an artifact, not a result.
- D-04 max_tokens: agent measures how many tokens each label takes in the hosted and the small tokenizers, proposes the smallest safe value with margin, Felipe approves. Same logic for the small model's max_new_tokens, including the end-of-turn token.
- Calls: sequential or a small thread pool, bounded; retry ONLY on transport errors (timeouts, 5xx), never on content. Cache raw responses to disk keyed by sha256(frozen_config_hash + messages) so a crashed notebook does not re-query. The cache never changes a reported answer: first successful response wins, no re-rolls.
- Every call logs: id, messages hash, raw response, latency. Raw response preserved verbatim.

### 4.4 Small model fine-tune

- D-05 / DEC-01 model choice. Phase 2 (not now): fetch Unsloth's current docs (fine-tuning guide, memory requirements, supported models list). Propose 2 to 3 candidates in the 2 to 5B range with: why it fits T4 for QLoRA training AND inference, chat template behavior (thinking flag?), license, Unsloth support status. Felipe picks. T4 has no bf16 support: verify and use fp16 as the docs direct.
- Training data: all 900 train rows, via the same prompt builder as inference (C-11). Check token lengths against max_seq_length: NO truncation allowed (C-16).
- Loss masking (DEC-02, investigate and log): train on assistant tokens only versus full sequence. Agent states Unsloth's current recommendation from docs, Felipe decides. The assistant target must include the end-of-turn token so inference stops cleanly.
- Settings: Unsloth recommended defaults from the docs fetched in Phase 2 (Week 9 allows predefined settings and no validation set). One run. No eval dataset (validation is reserved). No search. Fixed seed, recorded. Record: LoRA rank/alpha/targets, lr, epochs/steps, batch and accumulation, optimizer, precision, max_seq_length, seed.
- Record: GPU name and memory (`nvidia-smi`), peak VRAM during training and inference (`torch.cuda.max_memory_allocated`), wall-clock training time (own timer AND trainer stats), trainable parameter count, total parameter count, adapter file size.
- Save adapter, then build the ZIP from EXACTLY `adapter_model.safetensors` and `adapter_config.json` at the ZIP root (D-06 root layout, no folder). Unsloth writes extra files: never zip the directory. Inspect `base_model_name_or_path` in adapter_config; it must identify the original base model (C-17). If the library rewrote it to a different repo id, DO NOT hand-edit silently: log as a decision, prove the reload works, and show Felipe.
- Do not change the tokenizer or chat template (the ZIP cannot carry a tokenizer). Assert the template string hash is identical at training and inference (C-18).
- Retrain rule (R-11): if any pre-training check fails or cannot be verified after training started, delete the adapter, restart the runtime, reload the ORIGINAL base model, retrain with a fresh adapter.

### 4.5 Saved-adapter inference (the only source of FT predictions)

- Section S6 is self-contained: extracts the ZIP to a NEW folder (not the training output dir), loads the exact base model id and its tokenizer fresh (delete the training model, `gc.collect()`, `torch.cuda.empty_cache()`), attaches the adapter from the extracted folder, applies the same prompt builder, greedy decoding, same max_new_tokens, same response processing.
- Response processing, exactly: decode only newly generated tokens (record the skip_special_tokens choice) into `raw_response`; `pred = raw_response.strip().upper()`; accepted only if exactly POSITIVE, NEUTRAL or NEGATIVE, else `INVALID`. No fuzzy matching, no punctuation stripping.
- Batch size: default 1 for determinism (D-07). If batching is used for speed, record size and padding side, and prove label equality against batch size 1 on a fixed train subset first.
- A labeled section "COMPLETE SAVED-ADAPTER INFERENCE EXAMPLE" classifies one review from title and text, shows raw response and label, and prints model id, tokenizer id, package versions (from `importlib.metadata`), and generation settings. It uses no training code and no hosted calls.
- All 300 FT predictions and prompt_examples.jsonl are generated here. FT scores in S8 are computed by reading the saved predictions file, not from in-memory variables.

### 4.6 Evaluation (S8, reads saved files only)

- Labels: three sentiment classes plus INVALID as a prediction-only value. Reference classes never include INVALID.
- Per-class recall = correct / reference count (INVALID counts against recall). Precision = TP / predicted-as-class (INVALID is in no class). F1 from these. Macro-F1 and balanced accuracy average over the three classes only. Compute by hand-written code AND cross-check with scikit-learn (sklearn's balanced accuracy mishandles prediction-only labels, so do not rely on it alone). T-03 pins this with a fixture.
- Report per approach: balanced accuracy, macro-F1, per-class P/R/F1, correct and incorrect counts overall and per class, INVALID count.
- Confusion matrices: rows reference, columns predictions, each row normalized to sum to 1 (INVALID column included in the normalization). Three side by side, same color scale, annotated. Add an INVALID column in all three if any approach has any INVALID. Enlarged matrix for the best macro-F1 approach. Tie-break fixed now: higher balanced accuracy, then alphabetical approach name. Declared before results exist.
- McNemar: for pairs (zero-shot vs few-shot, zero-shot vs fine-tuned, few-shot vs fine-tuned): 2x2 correct/incorrect by test ID, discordant counts b and c, `statsmodels.stats.contingency_tables.mcnemar(table, exact=True)`. Cross-check with `scipy.stats.binomtest(min(b,c), b+c, 0.5)` doubled (capped at 1). Report b, c, p. Note three unadjusted tests and small discordant counts as limits.
- Error analysis: lists of test reviews fixed by FT, broken by FT, wrong in all three. Selection rule fixed in advance: first N by filtered_index per list (N set by Felipe). No cherry-picking.
- Cost view: hosted calls and wall time per approach, FT training time, peak VRAM, adapter size.
- Optional analysis, only with Felipe's approval: accuracy on test reviews whose titles are star-words ("Five Stars" style), to show title leakage. Descriptive only, never used to tune.

### 4.7 Submission files (names are defaults, D-08)

submission/
- `a4_finetune.ipynb`: executed in Colab, outputs present, report at the bottom.
- `adapter.zip`: exactly two files at ZIP root.
- `ft_test_predictions.jsonl` (D-09 default JSONL to avoid CSV quoting problems; CSV is also allowed). Fields in this order: original_row, filtered_index, title, text, reference_label, prediction, raw_response. One record per test review, 300 total.
- `prompt_examples.jsonl`: 3 lines, one per reference class, chosen by fixed rule (first test review of each class by filtered_index). Fields: original_row, filtered_index, reference_label, messages (exact ordered role/content list passed to the chat template). The label appears in metadata only, never in messages.

All four files come from the SAME final top-to-bottom run (section 8.4).

### 4.8 Report (S10)

- Code-generated facts block (numbers cannot drift): models and parameter counts (hosted 35B total, about 3B active; small model from the actual loaded model), training settings, actual GPU, whether T4 was tested directly, training time, package versions, generation settings per approach, all metrics, McNemar results.
- Prose for the seven required topics is written by Felipe. The agent supplies a one-page evidence table per topic (file and cell references), no narrative.
- Concise, nontechnical reader. State limits plainly: one dataset, one small model, one few-shot set, one run per approach, hosted model not identical in size to the small model, star labels are noisy proxies.

## 5. Notebook structure (single file, generated then executed in Colab)

Section | Content
---|---
S0 | Title, CONFIG dict (every setting, one place), package versions, GPU report, secret loading
S1 | Raw download, `build_splits`, cross-check against split_data.zip, checks C-01 to C-10 (raise on failure)
S2 | Prompt templates, few-shot set, complete prompts for ONE test review under all three approaches (R-21), checks C-12, C-14, C-14b, C-15
S3 | FREEZE CHECK: recompute frozen_config hash, assert equal to the approved hash, else stop
S4 | Prediction generation, hosted: 4a zero-shot, 4b few-shot (300 each), raw responses saved
S5 | Fine-tuning: prepared-record checks C-11, C-16, train, timers, save adapter, build and verify ZIP (C-17)
S6 | SAVED-ADAPTER INFERENCE: extract ZIP, fresh load, COMPLETE INFERENCE EXAMPLE, 300 predictions, write predictions file and prompt_examples.jsonl (C-18 to C-20)
S7 | Pre-scoring checks C-13
S8 | RESULTS (separate section, reads saved files only): metrics, matrices, McNemar, error analysis, cost view
S9 | Artifact consistency: C-19 to C-22 recomputed in-notebook
S10 | Report (auto facts block + Felipe's prose)

Authoring: logic in `src/a4_helpers.py` (unit-tested locally). `tools/build_notebook.py` inlines the helper file into one cell so the notebook is self-contained, and converts `notebook_src/a4_cells.py` (jupytext percent format) into `build/a4_finetune.ipynb`. One source of truth. Never hand-edit the notebook JSON.

## 6. Repo layout and tooling

```
CLAUDE.md  PLAN.md  LOG.md  DECISIONS.md  .gitignore
docs/        assignment4.pdf  assignment4.txt  assignment1.pdf
data/        split_data.zip   raw/ (gitignored)
src/         a4_helpers.py
tests/       test_splits.py test_labels.py test_parse.py test_metrics.py test_mcnemar.py test_prompts.py
tools/       build_notebook.py  check_data.py  verify_submission.py  scan_secrets.py
notebook_src/a4_cells.py
build/       a4_finetune.ipynb (generated, unexecuted)
evidence/    gate reports, check logs, audit outputs
submission/  the four final files (from the final run only)
.claude/agents/  data-auditor.md metrics-auditor.md submission-verifier.md red-team.md
```

Deterministic scripts do the checking; subagents read script output and look for what scripts cannot catch. This is the main token saver.
Local Python: pytest, pandas, scikit-learn, scipy, statsmodels, nbformat, jupytext. Versions recorded in LOG.md after install (never from memory).
.gitignore: data/raw, *.gz, .env, any file matching `*key*`, `__pycache__`, `.ipynb_checkpoints`.

## 7. Phases and gates

Each phase ends with a Gate Report and a STOP. Commit at the gate after Felipe approves.

### Phase 0: Setup and discovery (no model or prompt decisions)
- [ ] Read this plan sections 0 to 2 and 7. Read Appendices A and B once.
- [ ] Create repo scaffold (section 6), CLAUDE.md (Appendix B), agent files (Appendix A), LOG.md, DECISIONS.md. Private git repo. Do not push.
- [ ] Copy assignment PDFs into docs/, make assignment4.txt with `pdftotext`. Ask Felipe for the Assignment 1 repo path; read ONLY its prompt and scoring files (reference, no copying of code without telling him).
- [ ] Read https://github.com/davedgd/colab-mcp README fully. Report its prerequisites and connection steps. Felipe has set up NOTHING yet: list every manual step he must do (browser, runtime, secrets, uploads).
- [ ] After Felipe connects: smoke test (run a trivial cell, print python version, `nvidia-smi`, confirm GPU is a T4). If the MCP cannot run cells with Claude Code, STOP and report options. Do not improvise a workaround.
- [ ] Endpoint probe from Colab (not your machine): list models, one real classification call on a TRAIN review, record latency. Investigate DEC-03 (thinking off) on 5 to 10 train reviews. Record exactly what was sent and received.
- [ ] Probe Colab package state (versions only). Do not install Unsloth yet.
- [ ] Ask the batched question list: everything in section 12 still open plus anything you discovered.
Gate G0: MCP works, T4 confirmed, endpoint reachable, thinking-off mechanism evidenced, all questions answered.

### Phase 1: Data layer (local, no GPU)
- [ ] Felipe provides the raw gz (or approves your download); record size and sha256.
- [ ] Write `src/a4_helpers.py` split builder, label mapping, parse_label, prompt builders (stubs until Phase 2), metrics, McNemar. Write tests first (T-01 to T-08).
- [ ] Run builder on raw. Compare to zip: C-01 to C-10. Include train ORDER equality (strong evidence for the Random(43) procedure).
- [ ] Anything unexpected (line counts, gap patterns in original_row, non-string text) is reported verbatim.
- [ ] Spawn data-auditor (independent re-derivation, no reuse of your code).
Gate G1: all C-01 to C-10 PASS with log in evidence/, tests green, auditor agrees. Felipe personally spot-checks IDs, class counts, overlap (the PDF tells him to).

### Phase 2: Decisions (research and approval, no training)
- [ ] Fetch current Unsloth docs: fine-tuning guide, memory requirements, supported models, recommended settings. Quote version/date seen. Note: Unsloth API names drift, so never write Unsloth code from memory.
- [ ] Present D-05 model candidates (DEC-01), D-03 few-shot shortlist, D-01/D-02 prompt wording, D-04 token limits, DEC-02 loss masking, D-06 to D-09 file conventions. One decision per DECISIONS.md entry: question, your recommendation, alternatives, evidence gathered, Felipe's choice.
- [ ] Felipe reads at least 20 formatted training examples with labels (PDF asks him to review several). Show them as the exact rendered chat-template text.
Gate G2: every D-xx answered and logged. Nothing frozen yet.

### Phase 3: Notebook build and dry run (still no test predictions)
- [ ] Write `notebook_src/a4_cells.py`, build the ipynb, run S0 to S2 in Colab. Dry-run plumbing ONLY on a handful of TRAIN reviews that are not few-shot examples: format validity, parser, timers. No accuracy-driven edits.
- [ ] Run a tiny training smoke (a few steps) ONLY to prove memory fit, speed, adapter save, ZIP build, reload. Then delete that adapter and restart the runtime. The smoke adapter must never be submitted. State this in LOG.md.
- [ ] Run metrics/McNemar code on SYNTHETIC predictions (fixtures), never on test.
- [ ] red-team (Opus) pre-freeze audit: spec compliance matrix vs section 3, leakage hunt, check that no val or test labels are touched before S8.
Gate G3: red-team has no open P0/P1 findings, memory fit demonstrated, all T-tests green.

### Phase 4: Freeze
- [ ] `tools/freeze.py` writes `frozen_config.json` (prompt templates, few-shot ids, model ids, generation settings, max token values, seeds, instruction hash) and its sha256.
- [ ] Felipe replies literally `FREEZE APPROVED <first 8 chars of hash>`.
Gate G4: hash recorded in LOG.md. From here, section 8.3 applies.

### Phase 5: Hosted predictions
- [ ] Run S4 once for zero-shot and few-shot. Save raw responses. Report INVALID counts and empty-content counts. Do NOT look at accuracy to decide anything.
- [ ] If INVALID is high, first check the mechanical causes (thinking, token cap), report to Felipe, and wait. Any fix is an infrastructure fix, logged, applied to both prompts, and the whole hosted run repeats. Never choose between two runs by score.
Gate G5: 300 responses per approach, one per test ID, raw preserved.

### Phase 6: Final full run (single top-to-bottom, T4)
- [ ] Restart runtime, Run All. The same run trains, saves, zips, reloads, predicts, scores, and writes the report facts. Do not edit code mid-run.
- [ ] If it fails mid-run for an infrastructure reason: log it, fix, restart, run again from the top. If it fails a data check after training began: R-11 applies.
- [ ] Felipe downloads all artifacts from Colab (and copies to Drive if mounted) BEFORE closing anything.
Gate G6: R-01 to R-05, R-09 to R-12, R-17 to R-21, R-27 to R-31 PASS with evidence; no error outputs; all four files from this one run.

### Phase 7: Evaluation review and reload proof
- [ ] metrics-auditor recomputes everything from the downloaded files with an independent code path and compares to notebook outputs (C-21).
- [ ] Restart-runtime proof (C-25): fresh runtime, run ONLY S0 plus S6 against the downloaded ZIP and the downloaded predictions. Compare labels row by row to the submitted file. Record result. Any difference is investigated (batch, padding, nondeterminism). If a code fix is needed, Phase 6 repeats in full so all four files stay from one run.
- [ ] Error analysis lists generated under the fixed selection rule.
Gate G7: metrics reproduced independently, restart proof recorded, R-22 to R-25 PASS.

### Phase 8: Report, verification, handoff
- [ ] Draft evidence tables (section 4.8). Felipe writes the prose in the notebook S10 markdown cells (markdown edits after running are allowed by the PDF).
- [ ] `tools/verify_submission.py` and `tools/scan_secrets.py` on submission/. submission-verifier agent reads their output. red-team (Opus) final audit including the anchoring check: every claim in the prose is traced to a number in the saved outputs, nothing written to fit an expected narrative.
- [ ] Final consistency: report numbers equal outputs equal files (C-21, C-22).
Gate G8: R-15, R-16, R-26 to R-28, R-32 PASS. Felipe submits on Canvas manually.

## 8. Quality process

### 8.1 Check catalog (each is code that raises; results saved in evidence/ and printed in the notebook)

ID | Check
---|---
C-01 | Raw file readable; line count, sha256, size recorded
C-02 | Rebuilt (filtered_index, original_row) pairs equal the zip's for train, val, test
C-03 | Labels recomputed from rating equal reference_label on every row
C-04 | Index ranges: train 1000-19999, val 20000-29999, test 30000-39999
C-05 | Train selection reproduces the zip's records AND order from Random(43) procedure
C-06 | Test equals first 100 per class by file order within range
C-07 | Val equals first 100 per class; static scan proves no code after S1 reads val
C-08 | Set sizes and class counts printed: 900 and 300 per class; 300 and 100 per class
C-09 | Unique ids within each set
C-10 | No shared ids across sets
C-11 | Dataset object actually handed to the trainer: exactly the 900 ids, 300 per class, text matches source title/text, no rating field, label only in assistant turn
C-12 | Few-shot ids subset of train, disjoint from val and test, and the few-shot turns inside the actual prompts match those records
C-13 | Per approach: exactly one prediction per test id, no duplicates, no missing, set equality with the 300 test ids
C-14 | Prompt builders return identical output when rating and reference_label are altered (sentinel test)
C-14b | Instruction text hash identical across zero-shot, few-shot, fine-tuned prompts
C-15 | No test-derived field other than title and text appears in any built prompt
C-16 | No train or test example truncated by max_seq_length (token counts checked)
C-17 | ZIP namelist equals exactly the two names at root; adapter_config base id identifies the original base model
C-18 | Reload used a fresh model instance and the extracted folder; chat template hash equals training time hash
C-19 | Predictions file: 300 rows, exact field names and order, ids equal test ids, prediction in allowed set
C-20 | prompt_examples: 3 rows, one per class, each equals the rebuilt messages of its prediction record, no label inside messages
C-21 | Metrics recomputed from the saved predictions equal what the notebook displayed
C-22 | Every number in the report equals a number in saved outputs (scripted extraction)
C-23 | Secret scan on notebook source and outputs, repo, and evidence files
C-24 | Notebook: every code cell executed, zero error outputs
C-25 | Restart-runtime reload reproduces the submitted predictions
C-26 | Freeze hash matches the approved hash at S3 and in the final run

### 8.2 Unit tests (local, before Colab)

- T-01 builder on a synthetic file: blank lines, 2-char text, whitespace-only text, missing text, original_row counts blanks.
- T-02 label boundaries at ratings 1, 2, 3, 4, 5 and invalid ratings.
- T-03 metrics fixture hand-computed, includes INVALID predictions: recall denominators, precision, balanced accuracy, macro-F1, row normalization sums to 1 with INVALID column.
- T-04 parse_label: "POSITIVE", " positive\n", "Positive.", "", "POSITIVE NEGATIVE", "Neutral" with expected outputs, strict.
- T-05 McNemar: fixture b=10, c=2 should give 158/4096 (about 0.0386). Verify by running, do not trust this line. Compare statsmodels with the binomial cross-check, include b+c=0.
- T-06 prompt builders: determinism, exact format, few-shot ordering, invariance (C-14).
- T-07 ZIP builder refuses extra files; verifier fails on a ZIP with three files.
- T-08 prediction writer and reader round trip with newlines, quotes, unicode, and whitespace in raw_response.

### 8.3 Freeze protocol

Before Phase 4 anything may change with Felipe's approval. After `FREEZE APPROVED`, any change to prompts, few-shot ids, model ids, token limits or settings requires: explicit Felipe approval, a DECISIONS.md entry, a statement that no test result motivated it, and a full rerun of every affected approach. Test results seen so far must be disclosed in the entry. S3 enforces the hash.

### 8.4 One-run rule and rerun policy

- All four files and the executed notebook come from one complete top-to-bottom run. Never rerun the training cell after the final run: it would produce a different adapter than the ZIP you submit.
- Each approach touches the test set once per complete run. A rerun is allowed only for infrastructure failure (timeout, disconnect, OOM, install error), logged with cause. Never keep the better of two runs. Never rerun because a score looks disappointing.
- Hosted outputs may vary between runs (the PDF allows this). Report the final run as is.

### 8.5 Failure handling

- Any failed check: stop, print the failing ids, report, wait.
- Trained on unverified rows: delete adapter, restart runtime, retrain from the original base with a fresh adapter (R-11).
- Colab disconnects: artifacts live only in the runtime. Write to Drive if mounted and tell Felipe which files exist where.
- Never "fix" a check by loosening it.

### 8.6 Gate report format: see Appendix C. Max 300 words plus evidence paths.

## 9. Agents, model routing, token budget

### 9.1 Agents (definitions in Appendix A)

Agent | Model | Purpose | Runs at
---|---|---|---
main (builder) | Sonnet 5.5 | writes code, runs tools, Colab MCP | all phases
data-auditor | Sonnet 5.5 | independent re-derivation of splits and prepared records | G1, G6
metrics-auditor | Sonnet 5.5 | independent metrics and McNemar from files, no shared code | G7
submission-verifier | Sonnet 5.5 | reads verify_submission and scan_secrets output, inspects the four files | G8
red-team | Opus 5.5 | spec matrix, leakage hunt, anchoring check | G3 and G8 only

Caveat (honest): the Bash tool cannot be made read-only. Auditors have no Write/Edit tools, and the main session runs `git status --porcelain` after each audit and aborts if anything changed. Auditors return at most 250 words plus file paths; the main session saves the report to evidence/.
Confirm model availability with `/model` in Phase 0. If Opus 5.5 is unavailable on Felipe's plan, report it and fall back to Sonnet 5.5 with a stricter checklist; do not silently substitute.

### 9.2 Skills and MCP

- Enable ONLY the Colab MCP server. Each extra MCP server adds tool schemas to every turn (token cost) and attack surface. No third-party skills or plugins.
- No custom skills required: deterministic `tools/` scripts replace them and cost no context. Optional later: wrap `tools/verify_submission.py` as a project skill if Felipe wants.

### 9.3 Token optimization rules

1. Develop and test locally with pytest first. Colab round trips are the expensive path.
2. Cap output on every command. Colab cell outputs: disable progress bars, log training every coarse step interval, print summaries not rows.
3. Through Colab MCP read only the specific cell outputs you need, never the whole notebook.
4. `/clear` after each gate. LOG.md and DECISIONS.md are the memory. Start of session reads follow section 0.
5. Docs: fetch only the Unsloth pages needed, extract the settings you need into DECISIONS.md, do not keep pages in context.
6. Subagents return short reports. Scripts print PASS/FAIL tables.
7. Opus only at G3 and G8. Everything else Sonnet.
8. Do not paste the assignment, the plan, or the dataset into subagent prompts: point to file paths and requirement IDs.

## 10. Risk register

Risk | Why it matters | Control
---|---|---
Colab MCP with Claude Code is untested (the course tested Hermes) | Setup can eat the schedule | Phase 0 smoke test; stop and report on failure
T4 availability, usage limits, idle disconnects | Training or final run lost | Schedule buffer; Drive copy; keep final run short and single
Thinking not truly disabled on hosted model | Empty responses become mass INVALID, a fake result | DEC-03 evidence before freeze; empty-content count reported
Unsloth or bitsandbytes install or API drift on T4 | Broken run, stale agent knowledge | Fetch docs, record versions, never code Unsloth from memory
Rerunning notebook retrains a different adapter | Submitted ZIP no longer matches predictions | One-run rule (8.4)
Batch or padding nondeterminism in 4-bit generation | Restart proof fails | Batch size 1 default, C-25
Adapter ZIP wrong contents or base id rewritten | Automatic fail of R-27 | C-17, T-07, DEC log
Title leakage ("Five Stars") inflates all approaches | Misleading conclusions | Keep titles as provided, disclose, optional descriptive analysis
Prompt or few-shot tuned on test by accident | Invalidates evaluation | Freeze protocol, validation reserved, hash check
Label noise: 3-star is a weak proxy for neutral | Errors may be label problems, not model problems | Show examples, state limit in report
Three unadjusted McNemar tests, small discordant counts | Over-reading p-values | Report b, c, note limits
Report written by agent, not by Felipe | Violates the individual learning requirement | Rule 10, evidence tables only
Credential leak | Key is in the assignment text | Secrets only, C-23 scan
Agent anchoring on expected result | Narrative written to fit | red-team anchoring check, fixed selection rules for examples

## 11. Schedule (ASSUMED deadline Fri 2026-10-30, confirm)

Day | Plan
---|---
Mon 10-26 | Phase 0, Phase 1 (G0, G1)
Tue 10-27 | Phase 2, Phase 3 (G2, G3)
Wed 10-28 | Phase 4, Phase 5, Phase 6 final run (G4 to G6). Training time itself is not the bottleneck; debugging is.
Thu 10-29 | Phase 7, Felipe writes report prose, Phase 8 verification (G7, G8 draft)
Fri 10-30 | Buffer day, Felipe submits on Canvas. No new work after G8 unless a gate failed.

If the real deadline is earlier, compress by merging G2 and G3 reviews, never by skipping checks.

## 12. Open items for Felipe (ask in the Phase 0 batch)

1. Real Canvas deadline and time of day.
2. Path to the Assignment 1 repo (prompt and scoring files for reference).
3. Colab tier. T4 required; confirm one is actually obtainable. Is a paid tier needed or available?
4. Confirm Opus 5.5 is available in Claude Code on his plan.
5. Colab Secrets set up for the class key (name the secret `CLASS_API_KEY`), Drive mounted or not.
6. Submission file names and format defaults (D-06 to D-09): ZIP files at root; JSONL predictions; names in section 4.7.
7. How many items in the error-analysis lists (N).
8. Any rubric or Canvas announcement beyond the PDF.
9. Is optional title-leakage analysis (section 4.6) wanted?

## 13. Manual steps only Felipe can do

- Open Colab in Chrome, select a T4 runtime, follow the colab-mcp connection steps.
- Add the API key to Colab Secrets; upload split_data.zip to the Colab session; mount Drive if wanted.
- Approve each gate with `GO Gx` and the freeze with `FREEZE APPROVED <hash8>`.
- Download all artifacts from Colab before leaving. Runtime storage is temporary.
- Write the report prose. Personally verify IDs, class counts and overlap.
- Submit the four files on Canvas.

## Appendix A: Agent definitions (create once in Phase 0 under .claude/agents/, then never re-read)

File: .claude/agents/data-auditor.md
```
---
name: data-auditor
description: Independently re-derives the Assignment 4 splits and checks prepared training records. Read-only. Use at G1 and G6.
tools: Read, Grep, Glob, Bash
model: sonnet
---
You audit data integrity for MBAX 6418 Assignment 4. You may not edit files. Use Bash only for read-only commands and for running scripts under tools/.
Do NOT import or reuse src/a4_helpers.py. Write your own throwaway code in /tmp to rebuild the splits from the raw gz following PLAN.md section 4.1, then compare to data/split_data.zip and to the files named by the caller.
Verify: C-01 to C-10 and, when given a trainer dataset dump, C-11 and C-12. Report each as PASS/FAIL with the evidence (counts, first mismatching id).
Report at most 250 words plus file paths. State anything surprising even if all checks pass. Never say PASS without having computed it yourself.
```

File: .claude/agents/metrics-auditor.md
```
---
name: metrics-auditor
description: Independently recomputes all Assignment 4 metrics and McNemar tests from the saved prediction files. Read-only. Use at G7.
tools: Read, Grep, Glob, Bash
model: sonnet
---
You recompute evaluation results for MBAX 6418 Assignment 4 without sharing code with the notebook. No edits. Bash read-only plus /tmp scripts.
Inputs: the three prediction files and the notebook's displayed numbers.
Rules (PLAN.md 4.6): classes are POSITIVE, NEUTRAL, NEGATIVE; INVALID is a prediction-only value counted incorrect; recall uses reference counts; precision uses predicted-as-class counts; macro averages over the three classes only; row-normalized confusion matrices include an INVALID column when any exists; McNemar exact on ID-aligned correctness (use scipy binomial test as your path, compare with the notebook's statsmodels p).
Align by id, never by position. Report every number that differs from the notebook, with both values. At most 250 words plus file paths.
```

File: .claude/agents/submission-verifier.md
```
---
name: submission-verifier
description: Inspects the four final submission files and the notebook for Assignment 4 compliance. Read-only. Use at G8.
tools: Read, Grep, Glob, Bash
model: sonnet
---
You verify the final submission for MBAX 6418 Assignment 4. No edits.
Run tools/verify_submission.py and tools/scan_secrets.py, then inspect independently: ZIP namelist is exactly adapter_model.safetensors and adapter_config.json at root; adapter_config base model identifies the original base; predictions file has 300 rows, exact fields in order, ids equal the test ids; prompt_examples.jsonl has 3 rows, one per class, each matching its prediction record, no label inside messages; the notebook has no error outputs and no unexecuted code cells; report numbers match saved outputs.
Output a requirement table (R-15, R-27 to R-32) with PASS/FAIL and evidence. At most 250 words plus file paths.
```

File: .claude/agents/red-team.md
```
---
name: red-team
description: Adversarial audit of Assignment 4 for spec gaps, leakage and narrative anchoring. Read-only. Use at G3 and G8 only.
tools: Read, Grep, Glob, Bash
model: opus
---
You are a hostile reviewer for MBAX 6418 Assignment 4. No edits. Be brutal and specific.
1. Spec matrix: for each R-xx in PLAN.md section 3, mark PASS, FAIL or UNVERIFIED with a file or cell reference. Check PLAN.md against docs/assignment4.txt for requirements the plan missed.
2. Leakage hunt: any path where rating, reference_label, validation data, or test results can reach a prompt, a training record, a few-shot example, or a setting. Check the freeze hash logic.
3. Reproducibility: anything that makes the submitted ZIP, predictions, prompt examples and notebook disagree.
4. At G8 only, anchoring check: for every claim in the report prose, find the number in the saved outputs that supports it. Flag claims that echo what the assignment or class slides hint should happen but are not supported by the data. Disagreement with an expected story is a positive finding.
Severity: P0 blocks submission, P1 must fix, P2 note. At most 400 words plus file paths. Do not soften findings.
```

## Appendix B: CLAUDE.md content (create in Phase 0, keep under 40 lines)

```
# CLAUDE.md (MBAX 6418 Assignment 4)
- Plan: PLAN.md. Requirements win from docs/assignment4.pdf. Read PLAN.md sections 0-2 and the ACTIVE phase only.
- Session start: tail -n 40 LOG.md. After each gate: /clear.
- Assume nothing. No versions, model sizes, VRAM or hyperparameters from memory: fetch or measure. Ask all questions in one batch.
- Tag claims [VERIFIED: path] or [UNVERIFIED].
- Gates: output the Gate Report, STOP, proceed only on "GO Gx". Freeze only on "FREEZE APPROVED <hash8>".
- Validation set is reserved. Test labels are read only in S8 scoring. Prompt builders take (title, text) only.
- Secrets never in files or outputs. Class key from Colab Secrets or env var CLASS_API_KEY.
- No em dashes anywhere. Report prose is Felipe's, not yours.
- Never commit without showing git status and message. Never push or submit to Canvas without explicit instruction.
- Cap command output. Local pytest before Colab. Only the Colab MCP server is enabled.
- Models: Sonnet 5.5 default, Opus 5.5 only for red-team at G3 and G8. Confirm availability with /model.
- Log every decision in DECISIONS.md and every gate, seed, setting and run in LOG.md.
```

## Appendix C: Gate Report template

```
GATE Gx REPORT  (max 300 words)
Phase: <name>      Date: <date>      Commit candidate: <short hash or none>
Checks: <ID: PASS/FAIL, evidence path>  (one line each)
Requirements advanced: <R-xx list with PASS/UNVERIFIED>
Anomalies and surprises: <everything odd, even if harmless>
Decisions needing Felipe: <list or none>
Unverified claims still open: <list or none>
Audit: <agent, verdict, path to saved audit>
Next: <next phase, what you will do after GO>
STOP. Awaiting "GO Gx".
```
