"""Phase 2 token and chat-template measurements on TRAIN rows only (no val, no test).

Usage: python tools/phase2_tokens.py > evidence/phase2_token_measurements.log
"""
import hashlib
import json
import os
import re
import statistics
import sys
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import a4_helpers as h  # noqa: E402
from transformers import AutoTokenizer  # noqa: E402

z = zipfile.ZipFile("data/split_data.zip")
train = [json.loads(x) for x in z.read("train.jsonl").decode("utf-8").split("\n") if x.strip()]
assert len(train) == 900

CANDS = {
    "qwen3-4b": "unsloth/Qwen3-4B-unsloth-bnb-4bit",
    "llama3.2-3b": "unsloth/Llama-3.2-3B-Instruct-bnb-4bit",
    "phi4-mini": "unsloth/Phi-4-mini-instruct-unsloth-bnb-4bit",
    "gemma3-4b": "unsloth/gemma-3-4b-it-unsloth-bnb-4bit",
}
HOSTED = ["Qwen/Qwen3.6-35B-A3B", "cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit"]


def pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(q * (len(xs) - 1))))]


def report(name, repo, kw=None):
    kw = kw or {}
    print(f"\n=== {name}: {repo}")
    tok = AutoTokenizer.from_pretrained(repo)
    tmpl = tok.chat_template if isinstance(tok.chat_template, str) else json.dumps(tok.chat_template)
    print("chat_template sha256:", hashlib.sha256(tmpl.encode()).hexdigest()[:16], "| len", len(tmpl))
    print("template uses strftime_now:", "strftime_now" in tmpl, "| mentions enable_thinking:", "enable_thinking" in tmpl)
    print("eos_token:", tok.eos_token, "| pad_token:", tok.pad_token, "| padding_side:", tok.padding_side)
    # label token lengths, bare and with the assistant end-of-turn as rendered by the template
    m = h.build_messages_fine_tuned("t", "x", target="NEUTRAL")
    full = tok.apply_chat_template(m, tokenize=False, **kw)
    prompt = tok.apply_chat_template(m[:-1], tokenize=False, add_generation_prompt=True, **kw)
    print("prompt is prefix of full:", full.startswith(prompt))
    print("rendered tail after generation prompt:", repr(full[len(prompt):]) if full.startswith(prompt) else "N/A")
    print("generation prompt tail:", repr(prompt[-80:]))
    for lab in h.LABELS:
        mm = h.build_messages_fine_tuned("t", "x", target=lab)
        f = tok.apply_chat_template(mm, tokenize=False, **kw)
        p = tok.apply_chat_template(mm[:-1], tokenize=False, add_generation_prompt=True, **kw)
        tail = f[len(p):] if f.startswith(p) else None
        n_bare = len(tok(lab, add_special_tokens=False)["input_ids"])
        n_tail = len(tok(tail, add_special_tokens=False)["input_ids"]) if tail is not None else None
        print(f"  {lab}: bare tokens={n_bare}; assistant span incl. end-of-turn tokens={n_tail}")
    lens = []
    for r in train:
        mm = h.build_messages_fine_tuned(r["title"], r["text"], target=r["reference_label"])
        s = tok.apply_chat_template(mm, tokenize=False, **kw)
        lens.append(len(tok(s, add_special_tokens=False)["input_ids"]))
    print(f"train rendered length (tokens), n={len(lens)}: min={min(lens)} median={statistics.median(lens)} "
          f"p95={pct(lens, .95)} p99={pct(lens, .99)} max={max(lens)}")
    print("train rows over 512 / 1024 / 2048 tokens:", sum(l > 512 for l in lens), sum(l > 1024 for l in lens),
          sum(l > 2048 for l in lens))


for name, repo in CANDS.items():
    try:
        report(name, repo)
    except Exception as e:  # report, do not hide
        print(f"\n=== {name}: {repo}\nERROR {type(e).__name__}: {str(e)[:300]}")
try:
    report("qwen3-4b enable_thinking=False", CANDS["qwen3-4b"], {"enable_thinking": False})
except Exception as e:
    print("ERROR qwen3 no-think", str(e)[:300])

for repo in HOSTED:
    try:
        tok = AutoTokenizer.from_pretrained(repo)
        print(f"\n=== hosted tokenizer {repo}")
        for lab in h.LABELS:
            print(f"  {lab}: bare tokens={len(tok(lab, add_special_tokens=False)['input_ids'])}")
        print("  eos:", tok.eos_token)
        break
    except Exception as e:
        print(f"\n=== hosted tokenizer {repo}: ERROR {type(e).__name__}: {str(e)[:200]}")
