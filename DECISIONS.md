# DECISIONS.md

One entry per decision: question, recommendation, alternatives, evidence gathered, Felipe's choice, date.

## Open

- D-01 prompt wording reconciled with Assignment 1 (Phase 2)
- D-02 NEUTRAL guidance in prompt (Phase 2)
- D-03 few-shot k and selection (Phase 2)
- D-04 max_tokens / max_new_tokens (Phase 2)
- D-05 / DEC-01 small model choice (Phase 2)
- DEC-02 loss masking (Phase 2)
- DEC-03 thinking off: APPROVED 2026-10-26, Colab re-run DONE 2026-10-26 (consistent, details below)
- DEC-05 hosted output not fully deterministic at temperature 0 (found in Phase 0, decide in Phase 2)

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
- Felipe's choice: pending.

### DEC-04 colab-proxy-mcp tool timeout (2026-10-26)
- Question: open_colab_browser_connection never returned inside the 30 s client timeout set in .mcp.json, and the abort shut the colab-mcp server down (server log 15:10:15 "Closing WebSocket server", process exited). Details in LOG.md, Phase 0 session 2.
- Evidence: the tool waits for a human click in the browser (handshake), then polls the notebook tool list for up to 10 s (session.py TOOLS_READY_TIMEOUT); UI_CONNECTION_TIMEOUT is 60 s. Both exceed 30 s together.
- Options: (A) raise the timeout to 120000 ms and restart; (B) investigate the hang first.
- Recommendation: A, since 120 s covers the 60 s handshake wait plus the 10 s tool poll.
- Felipe's choice (2026-10-26): A. .mcp.json colab-proxy-mcp "timeout" changed 30000 -> 120000. If the call still hangs, go to B.
