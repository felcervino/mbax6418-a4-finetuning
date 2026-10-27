"""Phase 3: why did C-18 fire? Compare the chat templates of the original Phi-4-mini tokenizer and Unsloth's mirrors.
Train rows only. Usage: python tools/phase3_template_diff.py > evidence/phase3_template_diff.log
"""
import difflib
import hashlib
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import a4_helpers as h  # noqa: E402
from transformers import AutoTokenizer  # noqa: E402

REPOS = ["microsoft/Phi-4-mini-instruct", "unsloth/Phi-4-mini-instruct", "unsloth/Phi-4-mini-instruct-unsloth-bnb-4bit"]
toks = {}
for r in REPOS:
    t = AutoTokenizer.from_pretrained(r)
    toks[r] = t
    print(f"{r}: template sha256 {hashlib.sha256(t.chat_template.encode()).hexdigest()[:16]} len {len(t.chat_template)} "
          f"eos={t.eos_token!r} pad={t.pad_token!r} bos={t.bos_token!r}")
base = toks[REPOS[0]].chat_template
for r in REPOS[1:]:
    print(f"\n--- unified diff: {REPOS[0]} -> {r}")
    for line in difflib.unified_diff(base.splitlines(), toks[r].chat_template.splitlines(), lineterm="", n=0):
        print(line[:300])
m = h.build_messages_fine_tuned("Five Stars", "Loved it.", target="POSITIVE")
for r in REPOS:
    t = toks[r]
    print(f"\n=== {r}")
    print("train render      :", repr(t.apply_chat_template(m, tokenize=False)))
    print("generation prompt :", repr(t.apply_chat_template(m[:-1], tokenize=False, add_generation_prompt=True)))
a = toks[REPOS[0]].apply_chat_template(m[:-1], tokenize=False, add_generation_prompt=True)
for r in REPOS[1:]:
    b = toks[r].apply_chat_template(m[:-1], tokenize=False, add_generation_prompt=True)
    print(f"generation prompt identical to microsoft original for {r}:", a == b)
