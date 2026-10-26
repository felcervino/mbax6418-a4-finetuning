# DECISIONS.md

One entry per decision: question, recommendation, alternatives, evidence gathered, Felipe's choice, date.

## Open

- D-03 few-shot k and selection: k=6 not yet confirmed; Felipe picks examples after reading evidence/phase2_fewshot_shortlist.md
- Accepted 2026-10-26 (see Phase 2 proposals): D-01, D-02, D-04, D-05/DEC-01, DEC-02, training settings
- DEC-03 thinking off: APPROVED 2026-10-26, Colab re-run DONE 2026-10-26 (consistent, details below)
- DEC-05 accepted 2026-10-26: option a plus b

### DEC-03 (approved, confirmed from Colab)
- Question: how to disable thinking on http://dobolyi.com:9001/v1 for cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit.
- Docs: HF model card says Qwen3.6 thinks by default and does not support /think, /nothink soft switches; shows `"chat_template_kwargs": {"enable_thinking": False}`. vLLM reasoning docs: pass it via `extra_body`; reasoning is returned in `message.reasoning` (renamed from `reasoning_content`).
- Test (local machine, 2026-10-26, tools/probe_endpoint.py, evidence/phase0_endpoint_probe_local.jsonl): 8 TRAIN reviews (first 8 rows of train.jsonl: filtered_index 2114, 5555, 6660, 11005, 4447, 16700, 8849, 2359), temperature 0, PLAN 4.2 default prompt.
  - No flag, max_tokens 400 (2 reviews): finish_reason=length, 400/400 tokens are reasoning_tokens, content=None. A small max_tokens without the flag would give empty content (mass INVALID artifact confirmed real).
  - enable_thinking False, max_tokens 50 (8 reviews): finish_reason=stop, reasoning=null, reasoning_tokens=0, content is a bare label on 8/8, no <think> tags, completion_tokens 3 (POSITIVE, NEGATIVE) or 4 (NEUTRAL).
  - Server fingerprint: vllm-0.32.0-61cde1f9.
- Recommendation: send `chat_template_kwargs: {"enable_thinking": false}` on every hosted call; in every run assert reasoning is null, reasoning_tokens == 0, finish_reason == "stop", and record counts of any violation.
- Still required: same probe from Colab (PLAN Phase 0).
- Felipe's choice (2026-10-26): APPROVED. Send `chat_template_kwargs: {"enable_thinking": false}` on every hosted call, with the per-call assertions above. Re-run the probe from Colab once connected; if Colab results differ, reopen this decision.

## Decided

### G0 question batch answers (Felipe, 2026-10-26)
1. Deadline: end of day Friday 2026-10-30. Exact time not given; treat as 23:59 local [UNVERIFIED against Canvas].
2. Assignment 1 repo: https://github.com/felcervino/amazon-gift-cards-sentiment. Read only its prompt and scoring files, in Phase 2 for D-01.
3. Colab tier: free.
4. Models: follow PLAN 9.1 (Sonnet 5.5 builder, Opus 5.5 only for red-team at G3 and G8).
5. DEC-06 Drive: Felipe asked for Claude's recommendation. Recommendation adopted: mount Drive, used only to copy artifacts (adapter, predictions, evidence) after each long step. Reason: free tier plus idle disconnects (PLAN risk register); runtime files are deleted on disconnect. Felipe must approve the Google consent popup himself when the mount cell runs.
6. D-06 to D-09 submission defaults (ZIP at root, JSONL predictions, names in PLAN 4.7): APPROVED.
7. DEC-07 error-analysis N: Felipe asked for Claude's recommendation. Recommendation adopted: N = 10 per list (first 10 by filtered_index, rule fixed before any test result). Reason: readable in the report, enough to show patterns, small enough that Felipe can read every item.
8. Rubric or announcements beyond the PDF: none.
9. Optional title-leakage analysis (PLAN 4.6): wanted. Descriptive only, never used to tune.
10. Endpoints txt: moved from project root to Downloads\class-endpoints (1).txt (identical copy already at Downloads\class-endpoints.txt). .gitignore now also has `class-endpoints*`.
11. split_data.zip: moved back to data/split_data.zip (sha256 1e827e0f..., unchanged).
12. docs/ may be committed, including assignment4.pdf/.txt which contain the class key as printed in the PDF. Felipe's explicit choice; overrides PLAN rule 7 for these two files only. Repo is local with no remote.
13. Full raw Colab files downloaded: evidence/phase0_endpoint_probe_colab.jsonl (998479af...) and evidence/phase0_repeatability_colab.jsonl (bbc98b34...), hashes match the runtime. No key or auth header inside.

- Colab confirmation (2026-10-26, T4 runtime, cells ublPkT1DGZzS and S4IkiMLtHCdD, evidence/phase0_endpoint_probe_colab_summary.jsonl): same 8 train reviews, byte-identical prompts (messages_sha256 equal to local), same fingerprint vllm-0.32.0-61cde1f9. Thinking off: 8/8 plus 24/24 repeats finish_reason stop, reasoning null, reasoning_tokens 0, bare label content, no think tags. Thinking on, max_tokens 400: 2114 again length with 400/400 reasoning tokens and content null; 5555 this time stopped at 262 tokens (257 reasoning) with content "

POSITIVE" (local: length, content null). Decision stands.

### DEC-05 (open, Phase 2) hosted nondeterminism at temperature 0
- Evidence: review 16700, thinking off, identical prompt and server build: local NEUTRAL; Colab probe POSITIVE; Colab repeats NEUTRAL x3. 1 flip in 5 calls. The other 7 reviews were stable across 5 calls each (local 1, Colab 1, repeats 3). Thinking-on 5555 also differed between runs (length vs stop).
- Likely cause [UNVERIFIED]: server-side batching numerics in vLLM; not investigated.
- Why it matters: zero-shot and few-shot scores can move between runs. PLAN one-run rule (8.4) and saved raw responses become the source of truth.
- Options to weigh in Phase 2: (a) accept, run once, save raw, report the measured flip rate; (b) also measure the flip rate on N train reviews and report it; (c) repeat k times and majority-vote (changes the method, needs a strong reason).
- Felipe's choice (2026-10-26): option a plus b, see Phase 2 proposals.

### DEC-04 colab-proxy-mcp tool timeout (2026-10-26)
- Question: open_colab_browser_connection never returned inside the 30 s client timeout set in .mcp.json, and the abort shut the colab-mcp server down (server log 15:10:15 "Closing WebSocket server", process exited). Details in LOG.md, Phase 0 session 2.
- Evidence: the tool waits for a human click in the browser (handshake), then polls the notebook tool list for up to 10 s (session.py TOOLS_READY_TIMEOUT); UI_CONNECTION_TIMEOUT is 60 s. Both exceed 30 s together.
- Options: (A) raise the timeout to 120000 ms and restart; (B) investigate the hang first.
- Recommendation: A, since 120 s covers the 60 s handshake wait plus the 10 s tool poll.
- Felipe's choice (2026-10-26): A. .mcp.json colab-proxy-mcp "timeout" changed 30000 -> 120000. If the call still hangs, go to B.

## Phase 2 proposals (2026-10-26, accepted unless marked pending)

Docs seen 2026-10-26 via WebFetch (a small model summarizes each page, so values are [UNVERIFIED] until confirmed in a notebook; none of the pages shows a date or version): unsloth.ai/docs fine-tuning-llms-guide, lora-hyperparameters-guide, unsloth-model-catalog, unsloth-requirements, phi-4 tutorial. HF API metadata read directly (evidence/phase2_token_measurements.log, license lines in LOG.md).

### D-01 / D-02 prompt wording and NEUTRAL guidance
- Assignment 1 prompt (felcervino/amazon-gift-cards-sentiment, src/three_class_prompt.py, public repo): long system prompt, delimiters <<<TITLE_START>>>, injection warning, NEUTRAL defined as "genuinely mixed, lukewarm, or indifferent", JSON output {"label": ...}, max_tokens 60, enable_thinking false, same hosted model and temperature 0.
- PLAN default (Week 9 style): short system line, one-word reply, no NEUTRAL definition.
- Recommendation: default for all three approaches, no NEUTRAL guidance. Reason: the fine-tune target is the bare label, the JSON wrapper adds tokens and a failure mode with no benefit, and a NEUTRAL definition would be a modeling choice I cannot justify without peeking at behavior.
- Alternatives: (b) A1 prompt for all three with the training target changed to JSON; (c) default plus A1's one NEUTRAL sentence for all three.
- Cost of (a): not continuous with Assignment 1; say so in the report.
- Felipe's choice (2026-10-26): ACCEPTED the recommendation. D-01 default prompt, D-02 no NEUTRAL guidance.

### D-03 few-shot k and selection
- Recommendation: k = 6 (2 per class), fixed class order shuffled once by a recorded RNG; k = 9 is the alternative. Shortlist: evidence/phase2_fewshot_shortlist.md (6 per class from TRAIN, rule: text 150 to 450 chars, title not a star-word title, RNG constant 20261026, not Random(43)). Felipe reads each, picks 2 per class, including at least one hard NEUTRAL (mixed review).
- Note: 98 of 900 train titles are star-word titles; the shortlist excludes them by rule, which is a design choice, not a neutral one.
- PROPOSED SET (2026-10-26, awaiting Felipe's explicit yes after reading each text; Felipe said "use suggested" without naming ids, so this is my reading of it): k=6 and the first 2 per class in shortlist order (a rule, not a quality pick): POSITIVE 2749, 13547; NEUTRAL 11866, 16202; NEGATIVE 9440, 9272. Prompt order = shuffle with random.Random(20261028): 13547, 16202, 11866, 2749, 9272, 9440.
- Concerns to read before approving: 13547 is rating 4 but the text describes a confusing reload (mixed); 9272 is rating 1 but the text is a neutral-sounding inquiry; 11866 and 16202 are the hard NEUTRALs (mixed praise and complaint). These are noisy-label cases, which is realistic but may confuse a 6-shot prompt.
- Felipe's choice (2026-10-26): APPROVED the proposed set exactly: k=6, ids 13547, 16202, 11866, 2749, 9272, 9440 in that order (labels as listed above, 2 per class). Check: all six are in train and none is in test [VERIFIED: command output at approval time, not saved as a file].

### D-04 token limits
- Evidence: hosted tokenizer (Qwen/Qwen3.6-35B-A3B): POSITIVE 2, NEUTRAL 3, NEGATIVE 2 bare tokens; Phase 0 probe completion_tokens 3 or 4 including the end token [VERIFIED: evidence/phase2_token_measurements.log, DEC-03 notes].
- Small model (Phi-4-mini tokenizer): assistant span including end-of-turn 3 (POSITIVE, NEGATIVE) or 4 (NEUTRAL) tokens. Other candidates: Llama 3.2 3 or 4, Gemma 3 3 or 4, Qwen3-4B 8 or 9 with its think block when thinking is not disabled.
- Recommendation: max_tokens = 8 hosted, max_new_tokens = 8 small (about 2x the longest observed). Longer chatter is cut and recorded as INVALID, never repaired.
- Felipe's choice (2026-10-26): ACCEPTED the recommendation. max_tokens 8 hosted, max_new_tokens 8 small.

### D-05 / DEC-01 small model (needs T4 training and inference)
Measured on the 900 train rows with each candidate's own chat template (evidence/phase2_token_measurements.log): longest rendered example 365 to 400 tokens, none over 512, so max_seq_length 512 would truncate nothing (C-16 re-checks in the notebook).
| Candidate (Unsloth 4-bit mirror) | Params (HF) | License | Template facts [VERIFIED: log] | Concern |
|---|---|---|---|---|
| microsoft/Phi-4-mini-instruct (unsloth/Phi-4-mini-instruct-unsloth-bnb-4bit) | 3.84B | MIT | plain, no thinking flag, no date, ends with <|end|> | Unsloth docs fetched do not cover this model on a T4 or its response markers; markers derived from the rendered template (<|user|>, <|assistant|>), to be proven in the Phase 3 dry run |
| Qwen/Qwen3-4B (unsloth/Qwen3-4B-unsloth-bnb-4bit) | 4.02B | Apache-2.0 | has enable_thinking; default generation prompt lacks the empty think block that the training render adds | train/inference prompt mismatch unless enable_thinking=False in both; same family as the hosted model blurs the comparison [UNVERIFIED] |
| meta-llama/Llama-3.2-3B-Instruct (unsloth/Llama-3.2-3B-Instruct-bnb-4bit) | 3.2B | llama3.2 community | system header contains "Today Date: <run date>" via strftime_now | prompt text depends on the day; fixable with a fixed date_string, which edits the template call [VERIFIED date appears] |
| google/gemma-3-4b-it (unsloth/gemma-3-4b-it-unsloth-bnb-4bit) | 4.3B | gemma terms | system text merged into the first user turn | multimodal checkpoint; license terms |
- Docs-stated QLoRA minimum VRAM: 3B 3.5 GB, 7B 5 GB, "absolute minimum" [UNVERIFIED, doc summary]. T4 fit must be measured in Phase 3.
- Recommendation: Phi-4-mini-instruct (simplest deterministic template, permissive license). Fallback if the dry run fails: Gemma 3 4B, whose response markers the docs give.
- C-17 issue to decide: loading the Unsloth mirror will probably record the mirror id in adapter_config base_model_name_or_path [UNVERIFIED]. Recommendation: load by the original microsoft id with load_in_4bit and check the recorded id in the dry run.
- Felipe's choice (2026-10-26): ACCEPTED the recommendation. Phi-4-mini-instruct loaded by the original microsoft id; fallback Gemma 3 4B.

### DEC-02 loss masking
- Docs: train_on_responses_only masks the inputs and trains on completions only, "about 1% accuracy" claimed [UNVERIFIED, doc summary]. For Phi-4-mini the docs give no strings.
- Recommendation: assistant tokens only, including the end-of-turn token, because the label is 2 to 3 tokens and full-sequence loss would mostly train on the prompt. Marker strings from the rendered template; Phase 3 must prove by decoding the unmasked labels.
- Alternative: full-sequence loss.
- Felipe's choice (2026-10-26): ACCEPTED the recommendation. assistant tokens only, including end-of-turn.

### Training settings proposal (from docs summaries, to be re-confirmed in the notebook docs in Phase 3)
- r 16, lora_alpha 16, dropout 0, bias none, targets q/k/v/o/gate/up/down, lr 2e-4, weight decay 0.01, scheduler linear, seed 3407 (docs example value), gradient checkpointing "unsloth", per-device batch 2. Docs disagree on accumulation (4 on one page, 8 on another), epochs 1 to 3. Optimizer and T4 precision flags were not stated on the pages read: [UNVERIFIED], fetch from a current Unsloth notebook in Phase 3.
- Recommendation: accumulation 8 (effective 16, 57 steps per epoch), 2 epochs, no eval set, one run.
- Felipe's choice (2026-10-26): ACCEPTED the recommendation. settings as proposed (accumulation 8, 2 epochs, one run); optimizer and T4 flags still to be fetched in Phase 3.

### DEC-05 hosted nondeterminism
- Recommendation: option (a) plus a small measured flip rate (b): run each hosted prompt once for the reported result, and separately repeat 30 TRAIN prompts 3 times to report the flip rate. Option (c) changes the method.
- Felipe's choice (2026-10-26): ACCEPTED the recommendation. option a plus b (single reported run, separate 30 x 3 flip-rate measurement).

### D-06 to D-09 and DEC-07
- Already approved in the G0 batch (see Decided).

### Anomalies found in Phase 2 work
- 57 of 900 train texts contain "<br />"; 98 train titles are star-word titles (leakage, to flag in the report). Mojibake check: 0 train rows (an earlier suspicion was a console display artifact, verified with ascii()).
- WebFetch summaries omitted several settings the PLAN needs (optimizer, T4 flags, Phi-4-mini notes): not guessed.
