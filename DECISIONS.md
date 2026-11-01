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

## Phase 3 findings (2026-10-26)

### DEC-08 Unsloth notebook reference and chat-template risk (information, needs Felipe's awareness)
- Source read: unslothai/notebooks nb/Phi_4-Conversational.ipynb at repo commit bf2a56f8 (2026-10-26), saved to the session scratchpad. There is NO Phi-4-mini notebook in that repo (only Phi-4 14B, Phi-3.5 mini, Phi-3 medium, Llama 3.2, Gemma 3, Qwen3). The 14B notebook is a reference for API shape only. [VERIFIED: scratchpad phi4nb.json]
- API seen: FastLanguageModel.from_pretrained(model_name, max_seq_length, load_in_4bit), FastLanguageModel.get_peft_model(r=16, lora_alpha=16, lora_dropout=0, bias="none", use_gradient_checkpointing="unsloth", random_state=3407), SFTTrainer + SFTConfig (batch 2, accum 4, warmup_steps 5, lr 2e-4, optim "adamw_8bit", weight_decay 0.001, lr_scheduler_type "linear", seed 3407), train_on_responses_only(trainer) with no arguments, FastLanguageModel.for_inference(model), model.save_pretrained / tokenizer.save_pretrained. No explicit fp16/bf16 flags (dtype auto).
- Conflicts with the accepted settings: weight decay 0.001 in the notebook vs 0.01 on the docs page; accumulation 4 vs 8. Accepted settings win (0.01, 8); optimizer takes the notebook value adamw_8bit. [Flag to Felipe at G3.]
- RISK: the notebook replaces the tokenizer's chat template with Unsloth's get_chat_template(tokenizer, "phi-4"), which is the Phi-4 14B format and is NOT the Phi-4-mini template. PLAN 4.4 says never change the chat template. Plan: do NOT call get_chat_template; use the tokenizer's own template; assert the template hash equals the HF original at training and at reload (C-18); prove masking by decoding labels.

### DEC-09 DEVIATION: Colab driven through Claude in Chrome, not the Colab MCP (2026-10-26, Felipe's choice)
- Question: the Colab MCP server closed within 25 to 55 s of every successful connect (5 of 5 instances closed with no error line; details in LOG.md). PLAN Phase 0 says to stop and report options when the MCP cannot run cells.
- Options given: A drive Colab via Claude in Chrome, B retry the MCP once more, C Felipe runs cells himself.
- Felipe's choice: A. Claude may add cells, paste code, run them and read outputs in Felipe's Colab tab through Claude in Chrome. Claude must never read or type the API key. Allowed also: upload files to the runtime Files panel.
- Method: the notebook source is built locally and uploaded as files (build/a4_finetune.ipynb, tools/colab_runner.py); a short cell runs notebook cells through the runner and long steps run in a background thread with log files. Notebook content is unchanged by this; the final submitted notebook must still be one complete top-to-bottom run (Phase 6), which Felipe can do with Run all, or Claude can do the same way.
- Risk: typed code can be altered by the editor (auto-closing brackets), so only short commands are typed; all substantive code arrives by file upload.

### DEC-10 Unsloth loads its own variant of the Phi-4-mini tokenizer (found by check C-18 on Colab, 2026-10-26)
- Evidence [VERIFIED: evidence/phase3_template_diff.log, Colab cell8 AssertionError]: loading "microsoft/Phi-4-mini-instruct" through FastLanguageModel returned a tokenizer whose chat template differs from Microsoft's. Original: eos and pad <|endoftext|>, template appends <|endoftext|> after the last assistant turn. Unsloth mirror (unsloth/Phi-4-mini-instruct, same template as the bnb-4bit mirror): eos <|end|>, pad <|PAD_TOKEN|>-style token, no trailing <|endoftext|>. The generation prompt (system, user, <|assistant|>) is byte-identical for both. Vocabulary is the same.
- Consequence: the training target ends "<|end|>" (Unsloth) vs "<|end|><|endoftext|>" (original). Inference prompts are unaffected. A grader loading Microsoft's tokenizer with the adapter would stop generation at <|endoftext|>, not <|end|>.
- What I changed in the notebook (disclosed, not hidden): the C-18 assertion "template equals Microsoft original" was my own addition beyond the catalog (C-18 = fresh reload, extracted folder, template hash equals the TRAINING-time hash). It now records TEMPLATE_MATCHES_ORIGINAL and the eos/pad differences in the output and in the report facts; the train-equals-reload assertion stays. Training text is rendered with the tokenizer that is actually loaded and the same tokenizer is used at inference.
- Options for Felipe: (a) accept Unsloth's tokenizer for training and inference and state the difference in the report (recommended: smallest departure from the approved path, consistent train and inference); (b) force Microsoft's tokenizer into the trainer and inference (needs eos handling by hand, more code, more risk); (c) switch the base load id to the Unsloth mirror id and record it, which makes adapter_config name the mirror (C-17 risk).
- Felipe's choice: pending. Dry run continues with (a) because it only tests plumbing.

### DEC-11 LoRA target modules do not exist in Phi-4-mini under the approved names (found in the Phase 3 smoke, 2026-10-26)
- Evidence: Colab smoke reported 8,912,896 trainable parameters. That equals 32 layers x (o_proj 98,304 + down_proj 180,224) at rank 16, so only o_proj and down_proj were adapted. Module listing of layer 0 shows fused self_attn.qkv_proj, self_attn.o_proj, mlp.gate_up_proj, mlp.down_proj; there is no q_proj, k_proj, v_proj, gate_proj or up_proj. [VERIFIED: Colab cell output 16:39, transcribed in LOG.md]
- The approved list (q, k, v, o, gate, up, down) therefore silently adapted only 2 of 4 projection types. A change of target names is needed to honor the approved intent (all attention and MLP projections).
- Recommendation: target_modules = ["qkv_proj", "o_proj", "gate_up_proj", "down_proj"]. Expected trainable parameters at r=16: 32 x (131,072 + 98,304 + 311,296 + 180,224) = 23,068,672. New check C-27 asserts every target type is adapted in every decoder layer (also after reload).
- Alternative: keep the two-module adapter (cheaper, weaker, not what was approved).
- Felipe's choice: pending. The dry run is being repeated with the recommended names to measure memory and speed.

### DEC-12 adapter_config base_model_name_or_path names the Unsloth mirror (found in the Phase 3 smoke, 2026-10-26)
- Evidence: after loading microsoft/Phi-4-mini-instruct with FastLanguageModel and save_pretrained, adapter_config.json says base_model_name_or_path = "unsloth/Phi-4-mini-instruct-unsloth-bnb-4bit". The PDF requires the configuration to identify the original base model; PLAN 4.4/C-17 says not to hand-edit silently.
- Options: (a) keep as written and say in the report that Unsloth loads and records its 4-bit mirror of the original model (risk: a strict reader may see a different id than microsoft/Phi-4-mini-instruct); (b) rewrite the field to "microsoft/Phi-4-mini-instruct" before zipping, openly logged here and in the notebook output, and prove the reload from the extracted ZIP still works (it does not read this field in our S6 path, because the base is loaded by explicit id); (c) ask the instructor.
- Recommendation: (b), with both values printed in the notebook (original written by Unsloth, edited value) and C-17 asserting the edited value equals the loading id.
- Felipe's choice: pending.

### DEC-11 UPDATE (2026-10-26, 16:42): Unsloth cannot adapt Phi-4-mini's fused projections
- Retest with target_modules ["qkv_proj","o_proj","gate_up_proj","down_proj"]: new check C-27 failed (it did its job): LoRA module types attached = ['down_proj','o_proj'] only. The PEFT target regex that Unsloth 2026.10.9 builds (printed from model.peft_config['default'].target_modules, 347 chars) contains only q_proj|k_proj|v_proj|o_proj|gate_proj|up_proj|down_proj, whatever names are passed. So with Unsloth's own get_peft_model, Phi-4-mini can only be adapted on o_proj and down_proj (8,912,896 trainable parameters at r=16). [VERIFIED: Colab cell output, transcribed in LOG.md]
- Phi-4-mini now has three Unsloth-specific wrinkles: DEC-10 (Unsloth's tokenizer variant), DEC-11 (fused projections not adaptable), DEC-12 (mirror base id). None of them is an error in the pipeline; all are consequences of this model under this Unsloth version.
- Options for Felipe:
  (A) Switch the small model to one with standard projection names and re-run the dry run: Gemma 3 4B (the fallback already named in D-05; the Unsloth docs fetched gave its response-marker strings; multimodal checkpoint, gemma license) or Qwen3-4B (Apache-2.0; needs enable_thinking handled identically in training and inference). Costs one more dry run (about 15 minutes) and a new D-05 entry.
  (B) Keep Phi-4-mini with o_proj and down_proj adapted only (8.9M trainable, about 0.4 percent of 3.8B). Cheapest, but weaker and different from the approved "all projections"; must be stated plainly in the report.
  (C) Keep Phi-4-mini and wrap the Unsloth-loaded model with plain peft LoraConfig on the fused names. Not tested; risks conflicting with Unsloth's trainer patches and is a departure from "Unsloth QLoRA".
- Recommendation: (A) with Gemma 3 4B first, because its marker strings are in the docs I read and its template has no date or thinking switch. Qwen3-4B second. I have not tested either on Colab yet [UNVERIFIED].
- Felipe's choice: pending.

### D-05 re-decided: small model is Gemma 3 4B (Felipe, 2026-10-26, after DEC-11)
- Question: Phi-4-mini under Unsloth could adapt only o_proj and down_proj (DEC-11). Options were A switch, B keep two modules, C bypass.
- Felipe's choice: A, Gemma 3 4B (Qwen3-4B fallback). Confirmed in chat after his first reply "Yes" did not name an option.
- Evidence from the Unsloth Gemma 3 4B notebook (unslothai/notebooks, commit bf2a56f8, saved in the session scratchpad): FastModel.from_pretrained("unsloth/gemma-3-4b-it", load_in_4bit=True), FastModel.get_peft_model with finetune_vision_layers=False, finetune_language_layers=True, finetune_attention_modules=True, finetune_mlp_modules=True (no target_modules list), train_on_responses_only, training text built with the leading <bos> removed because the tokenizer adds it again. The notebook also calls get_chat_template(tokenizer, "gemma-3"); this notebook does NOT (tokenizer and template stay as shipped, per PLAN 4.4).
- google/gemma-3-4b-it is gated (manual approval) so it cannot be loaded in Colab without a token; the ungated copy unsloth/gemma-3-4b-it is loaded and quantized on load. The adapter's recorded base id will therefore name that copy (DEC-12 now concerns this id, still pending; PDF wants "the original base model").
- Superseded: DEC-10 (Phi tokenizer variant) and the fused-module part of DEC-11 no longer apply; the new checks (C-27 module coverage, C-11c single BOS, finite loss) stay.
- Approved training settings carry over unchanged (r 16, alpha 16, lr 2e-4, wd 0.01, batch 2 x accum 8, 2 epochs, adamw_8bit, seed 3407). max_seq_length 512, max_new_tokens 8 (D-04) need re-measuring with Gemma's tokenizer in the dry run.

### DEC-12 UPDATE (Gemma 3 4B run): adapter_config base id
- The dry run recorded base_model_name_or_path = "unsloth/gemma-3-4b-it-unsloth-bnb-4bit" (Unsloth maps the loaded id unsloth/gemma-3-4b-it to its 4-bit mirror). google/gemma-3-4b-it is gated, so a plain Hugging Face load of the original needs a license-accepted token.
- Options: (a) keep the id Unsloth wrote and say so in the report; (b) rewrite the field to "unsloth/gemma-3-4b-it" (the id the notebook loads) or "google/gemma-3-4b-it" (the original), openly logged, with the reload still proven from the extracted ZIP; (c) ask the instructor which id satisfies "original base model".
- Recommendation: (b) with "google/gemma-3-4b-it" only if Felipe confirms the instructor accepts the gated id, otherwise (a). Not decided.
- Felipe's choice (2026-10-26): (a) keep the id Unsloth writes, unsloth/gemma-3-4b-it-unsloth-bnb-4bit. CONFIG: adapter_base_id_override None, expected_adapter_base_id equal to that id, asserted by C-17 and frozen. The report must state that Unsloth records its 4-bit copy of the original weights and that google/gemma-3-4b-it is gated.

### G3 red-team findings and what was done (2026-10-26, red-team agent, Opus; report summarized here, not saved verbatim)
- P0 DEC-12 open (base id in adapter_config): C-17 now asserts the id equals CONFIG expected_adapter_base_id (frozen) and supports an openly printed override; the value itself is still Felipe's decision.
- P1 S6 not self-contained: fixed. S5c writes train_meta.json; S6a loads it, imports what it needs, frees training objects only if they exist, and S8/S10 read the meta file. A restart-then-S6 run is part of the dry-run re-test.
- P1 freeze hash omitted helper behavior: the hash now includes the rendered zero-shot, few-shot and fine-tuned prompts for a fixed probe and the parser table (canonical_prompt_fingerprint); an empty approved hash can no longer pass.
- P1 unpinned installs and unpinned model revisions: unsloth, unsloth_zoo, peft, bitsandbytes, accelerate pinned to the dry-run versions; hub revisions recorded and asserted (C-28). torchao and triton are left as the notebook recipe has them and are recorded.
- P1 hosted cache lost on restart: with USE_DRIVE the cache lives on Drive. OPEN QUESTION for Felipe: which run counts as the hosted result (see below).
- P1 BOS prefix only checked in training: C-29 added after reload.
- P1 static scan failed open: every code cell now needs a section tag, and exec(, eval(, globals(), ZIP_PATH, test.jsonl, val.jsonl are forbidden outside S0 and S1.
- P1 anchoring: the "small discordant counts" print and the title-leakage sentence were reworded to neutral statements.
- P2 left as is, with reason: predictions and prompt files are assembled in S8a because they need the sealed labels; HTTP 4xx stops the run (infrastructure failure policy); the approved DEC-05 flip-rate test and the approved title-leakage analysis are still to be built; Run All with in-process pip is untested because the dry run used the harness.

### Open question: which run produces the hosted results (needs Felipe)
PLAN 8.4 says all four files come from one final top-to-bottom run, while Phase 5 runs the hosted predictions before Phase 6. Recommendation: do not run the hosted calls before the final run. Phase 5 is skipped as a separate run: the final notebook run (Phase 6) makes the hosted calls once, with the cache on Drive so a crash does not re-roll answers. The DEC-05 flip-rate measurement (30 TRAIN prompts x 3) is a separate, labelled cell.

### Hosted-run policy (Felipe, 2026-10-26): final run only
Answer to the open question above: option recommended. The hosted calls are made once, inside the final top-to-bottom run (Phase 6), with the cache on Drive. Phase 5 is not run as a separate hosted run. The DEC-05 flip-rate cell stays a separately labelled cell.

### Title-leakage and DEC-05 flip-rate cell design (Felipe, 2026-10-26, answers in one batch, all recommended options)
- Star-word rule: reuse the Phase 2 regex STAR_TITLE from tools/phase2_shortlist.py (optional one word, then a digit or one..five, then star or stars, case-insensitive, anchored at the start of the title).
- Title-leakage output: count of star-title test reviews, their reference-label mix, and accuracy per approach on the star-title subset and on the remaining reviews. Descriptive only, computed in S8 from saved files, never used to tune.
- Flip rate: both hosted prompts (zero-shot and few-shot), 30 TRAIN reviews x 3 calls each, 180 extra hosted calls, made only in the final run (hosted-run policy) in a separately labelled cell that bypasses the reported-run cache.
- Flip sample: TRAIN rows only, the 6 few-shot ids excluded, 10 per class, drawn with random.Random(20261029). Seed and ids go into the frozen config.

### Pre-freeze red-team re-audit of the two analysis cells (2026-10-26, red-team agent, Opus; summarized, not saved verbatim)
- No P0. No path from val or test labels into prompts, training records, the flip measurement or the frozen config.
- P1-1 dry-run flip answers could be reused by the final run (same FROZEN_HASH in both modes, Drive cache): FIXED, flip cache folder is now flip_<MODE>_<approach>; cache hits are reported. Correction to the design entry above: the dry run does send 18 plumbing flip calls on TRAIN (1 per class x 3 repeats x 2 prompts); the reported flip rate comes only from the final run.
- P1-2 a crash mid-item could mix answers from two kernel sessions: FIXED, every hosted call now stores session_id and created_utc (kept in the cache), and the result lists mixed_session_ids.
- P1-3 S10 needed in-memory flip values (NameError after a restart; wall time near 0 on cache reads): FIXED, S10 rebuilds the flip result from hosted_flip_rate_raw.jsonl with helper flip_summary; cost is the sum of per-call latencies.
- P1-4 the local freeze hash was never compared with a Colab S3 hash: OPEN, needs a Colab dry run (S0 to S3 at least). Local candidate: 8a1f06f4.
- P1-5 star-title accuracy vs rest mixes the title effect with the class mix: FIXED in code by ADDING a within-class table (recall per reference class, star titles vs other titles) to the approved subset-vs-rest output, and renaming the section and helper to neutral names (star_title_breakdown, report key star_word_titles). This goes beyond Felipe's approved design (addition only, descriptive). PLAN.md line 107 says "Flag in the report that such titles leak the rating"; red-team calls that a pre-stated conclusion. PLAN is Felipe's file, left unchanged; his call.
- P2 fixed: final run asserts FLIP_RUN_IDS == FLIP_IDS; S4b header now says "not used for any prediction or setting"; flip_rate handles an empty set. P2 noted for the report: the 3 repeats are back to back in one run, so they measure short-term repeatability, not run-to-run variation (stated in report_facts "design").
- P1-4 CLOSED (2026-10-26 19:31): Colab S3 FROZEN_HASH on a fresh T4 runtime = 8a1f06f40c4f3f273bd8149f7b4c25a9c0b20005ae5b5b435ae51be7a0e9e111, identical to tools/freeze.py (evidence/phase3_dryrun_summary.md, pre-freeze dry run section).

### FREEZE (Phase 4, Gate G4)
- Felipe replied "FREEZE APPROVED 8a1f06f4" (2026-10-26). Full hash 8a1f06f40c4f3f273bd8149f7b4c25a9c0b20005ae5b5b435ae51be7a0e9e111 (frozen_config.json, frozen_config.sha256), equal in Colab S3 and tools/freeze.py. From here PLAN 8.3 applies: any change to prompts, few-shot ids, model ids, token limits or settings needs Felipe's approval, an entry here, a statement that no test result motivated it, and a full rerun. No test result has been seen.
- Still open at freeze (not part of the hash): keep or drop the within-class star-title table (P1-5); PLAN.md line 107 wording.
- Within-class star-title table (P1-5 addition): Felipe 2026-10-26: KEEP. PLAN.md line 107 wording: Felipe decides separately, still open.

### DEC-13 Infrastructure fix after freeze: literal U+2028 and U+2029 in helpers (Phase 6, 2026-10-26, Felipe approved)
- Failure [VERIFIED: Colab cell 1 output of the first Run all, 2026-10-26 about 19:59]: cell 1 (helpers) raised SyntaxError "unterminated string literal (detected at line 248)" at `write_predictions`. Cause [UNVERIFIED for Colab internals, VERIFIED locally: src/a4_helpers.py held one literal U+2028 and one literal U+2029 inside string literals]: Python accepts them, so pytest and the local compile check passed; Colab's editor treats them as line breaks and split the line. Run all stopped at cell 1. No later cell ran: no hosted call, no test data, no training.
- Fix: the two literals are now the escape sequences   and   in the same two `.replace` calls. Runtime behaviour is identical (the same characters are matched and still written as the 6-character escape text). New tests/test_no_unicode_line_breaks.py fails if U+2028, U+2029 or U+0085 appear literally in src/a4_helpers.py, notebook_src/a4_cells.py, the built notebook or the test itself, and checks write_predictions still escapes them (test failed first on the old source, then passed). pytest 103 passed (was 98).
- Freeze check: tools/freeze.py gives the same FROZEN_HASH 8a1f06f40c4f3f273bd8149f7b4c25a9c0b20005ae5b5b435ae51be7a0e9e111 and frozen_config.json is unchanged. No prompt, few-shot id, model id, token limit or setting changed. No test result, prediction or test label has been seen; no hosted call was made. Rebuilt notebook sha12 ff8ea1350ee0 (was 1518f1e0f101), 25 cells, static scan clean.
- Next: re-upload the rebuilt notebook, restart the runtime, Run all from the top.

### DEC-14 Infrastructure fix after freeze: retry the hosted cache write on a Drive-backed folder (Phase 6, 2026-10-26, Felipe approved)
- Failure [VERIFIED: Colab cell 6 (S4) output of Run all attempt 2, about 20:10, screenshot read]: FileNotFoundError [Errno 2] on os.replace of a ".tmp" file to its final name inside /content/drive/MyDrive/a4_out/hosted_cache/ (call_hosted, helpers). S0 to S3 had passed, including C-26 (frozen hash matches). The run stopped in S4; no scoring cell ran, no accuracy or prediction was looked at. Cause [UNVERIFIED]: Drive file-system lag with 4 worker threads; the tmp file was not visible at rename time.
- Disclosure: before the failure S4 made some hosted calls on the 300 TEST inputs (inputs only, no labels). Their answers may be in the Drive cache (key = frozen hash + messages, first answer wins). The rerun reuses them (from_cache is reported per record) and calls the API only for missing items. The first-answer-wins policy is the one approved in the hosted-run policy; nothing was chosen by score because no score was seen.
- Fix: new _write_cache_file in helpers: up to 6 attempts, each rewrites a uniquely named tmp file (flush, fsync), then os.replace; on OSError it removes the tmp, sleeps 0.5 s times the attempt number and retries; the last failure is raised, never swallowed. The hosted API is never called again because of a failed write. Two tests added in tests/test_hosted.py (simulated FileNotFoundError twice then success: one API call, cached afterwards, no stray .tmp; permanent failure: raises after one API call). The retry test failed on the old code first. pytest 105 passed.
- Freeze check: tools/freeze.py FROZEN_HASH 8a1f06f40c4f3f273bd8149f7b4c25a9c0b20005ae5b5b435ae51be7a0e9e111 unchanged, frozen_config.json untouched. No prompt, few-shot id, model id, token limit or setting changed. Rebuilt notebook sha12 cb1a448809c5 (was ff8ea1350ee0), 25 cells, static scan clean.
- Next: Felipe uploads the rebuilt notebook, then restart runtime and Run all from the top, reusing the same Drive cache.

### DEC-15 Restart-runtime proof (C-25): how it was run and two deviations (Phase 7, 2026-10-27)
- Procedure [VERIFIED: restart proof output, evidence/final_run/restart_proof_ft_raw.jsonl]: fresh T4 runtime (the previous runtime had been recycled overnight, so /content was empty), Colab copy of the notebook with all outputs cleared, then ONLY helpers, S0, S1, S2, S3, the S5a install, S6a, S6b and S6c were run. No hosted call, no training, no S5b, S5c or S8. C-26 PASS (hash 8a1f06f4), C-18 PASS (template hash 7de1c58e208eda46, same as the final run), C-29 PASS, C-27 PASS (238 modules). S6c: 300 predictions in 131.1 s, INVALID 0, not ended with EOS 0, peak VRAM 4.87 GB.
- Result: the new ft_raw.jsonl equals submission/ft_test_predictions.jsonl row by row on id order, prediction and raw_response (0 differences in 300). Prompts, n_new_tokens and ended_with_eos also equal the final run's ft_raw; only latency_s differs. C-25 PASS.
- Deviation 1, ZIP source: the 110 MB browser upload of submission/adapter.zip ran at about 3 MB per minute and was lost when the runtime was recycled. The ZIP was copied instead from Drive (MyDrive/a4_out/adapter.zip, written by the final run's persist step) and its sha256 was checked in the runtime: 538010294a1795394bc4557537649718f4d6068bda740d8a5cdf4d7350cb0bc9, size 110,316,837 bytes, equal to the shipped submission/adapter.zip (sha12 538010294a17, same size). So the file loaded is byte-identical to the submitted one, but it was not the literally downloaded copy.
- Deviation 2, S6a: while setting up I typed a shell command into the wrong cell and overwrote the S6a cell in the Colab copy (my error; the submitted notebook in submission/ is unaffected). S6a was then run from a file extracted programmatically from the S6a cell of submission/a4_finetune.ipynb (sha256 prefix d504cc1f54fe, 67 lines) with %run -i, so the code run equals the submitted code. S6b and S6c ran as their original cells. An earlier attempt also moved a partial 3,145,728 byte adapter.zip into place; it was never loaded and the runtime was later recycled.
- Side effect: the proof's S6c persist step overwrote Drive's a4_out/ft_raw.jsonl with the proof output (identical except latency_s). Drive is not a submission location.

### DEC-16 Report prose drafted by the assistant (Phase 8, 2026-10-27, Felipe's override)
- CLAUDE.md and PLAN rule 10 say the report prose is Felipe's. Felipe replied "You write the report" and, when asked, confirmed "Yes, draft it" and chose the Gemma 3 switch (DEC-10, DEC-11, D-05 re-decided) as the issue investigated with the agent.
- Result: the draft is in the last markdown cell of submission/a4_finetune.ipynb with a first line marking it DRAFT, copy in evidence/report_draft.md (the notebook before the edit is not kept in the repo; git has the G6 version). Sources: report_facts.json, train_meta.json, the notebook outputs, the saved prediction files, evidence/gate_G7_metrics_audit.md and DECISIONS.md. Example reviews use the DEC-07 rule (first ids by filtered_index in each list).
- Limits of the draft, stated for Felipe: it describes what is recorded (what the agent found and recommended, what Felipe chose); statements about how Felipe weighed the options are inferred from the record and need his confirmation. No result was changed to fit the text.
- C-22 (tools/verify_submission.py) now compares report numbers with report_facts.json plus the notebook's cell outputs, and accepts only numbers listed with a named source in evidence/report_number_sources.json (6 entries: 0.06, 150, 450, 23, 51, 8912896). C-22 matches by value, not meaning, so every claim was also checked by hand against the files (see LOG.md).

### DEC-17 Adapter base model id left as the Unsloth 4-bit copy (Felipe, 2026-11-01)
- Question: patch adapter_config.json to name google/gemma-3-4b-it? Rejected on the assistant's recommendation: it changes frozen_config expected_adapter_base_id (freeze hash 8a1f06f4), contradicts the executed output of the inference-example cell, and needs a Colab re-run with a new FREEZE approval; the gated original may not load without a token.
- Mitigation instead: a markdown "Base model note" in the inference-example section and the last paragraph of the report. Adapter, predictions and frozen hash unchanged.

### DEC-18 Markdown-only fixes after the Opus red-team (Felipe: yes, 2026-11-01)
- Fixed in markdown only (no code, outputs, adapter or frozen config touched): base-model note rewritten to name the exact id the adapter requires; "running this section without retraining" note added (train_meta.json and key/Drive dependency stated, standalone path not tested); McNemar and p-value explanation corrected; cost question now answered yes/no with conditions and the 30.4 s hosted timing; numbers from outside the notebook labeled as such; file references removed from the report; heading moved above the loading cell; stale refs/original (old email) deleted.
- Not fixed (need Colab or Felipe): axis labels on the confusion matrices, truncated class counts in S1 output, train_meta.json dependency in code, report authorship (Felipe's own rewrite of interpretation, cost and decision paragraphs).

### DEC-19 Interpretation paragraphs follow Felipe's answers (2026-11-01)
- Felipe answered seven questions one at a time: fine-tuned won with a caution; learned the NEUTRAL boundary but over-guesses NEUTRAL; real on these 300 but fragile; stress one run each, noisy star ratings, unequal model sizes; no for a one-off job, yes for repeated use; "mostly trusted the agent" on the Gemma 3 switch (stated plainly in the report); authorship note says judgments are his and the assistant drafted wording and data sections.
- Report cell updated accordingly (trimmed to about 1,000 words). Adapter, predictions, outputs and frozen config untouched.
