"""Phase 2: few-shot candidate shortlist (D-03) and 20 rendered training examples (TRAIN rows only).

RNG constants are recorded below and are NOT Random(43). Nothing here reads val or test.
Usage: python tools/phase2_shortlist.py [chat_template_repo]
"""
import json
import os
import random
import re
import sys
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import a4_helpers as h  # noqa: E402
from transformers import AutoTokenizer  # noqa: E402

SHORTLIST_SEED = 20261026   # few-shot candidate draw
DISPLAY_SEED = 20261027     # which 20 training examples to display
TEMPLATE_REPO = sys.argv[1] if len(sys.argv) > 1 else "unsloth/Phi-4-mini-instruct-unsloth-bnb-4bit"
STAR_TITLE = re.compile(r"^\s*(\w+\s+)?(\d|one|two|three|four|five)\s+stars?\b", re.I)

z = zipfile.ZipFile("data/split_data.zip")
train = [json.loads(x) for x in z.read("train.jsonl").decode("utf-8").split("\n") if x.strip()]
assert len(train) == 900


def eligible(r):
    # rule fixed before reading candidates: 150 to 450 chars of text, title is not a star-word title
    return 150 <= len(r["text"]) <= 450 and not STAR_TITLE.match(r["title"])


rng = random.Random(SHORTLIST_SEED)
lines = [f"# D-03 few-shot candidate shortlist (TRAIN rows only)",
         f"Rule: text length 150-450 chars, title not a star-word title; 6 candidates per class drawn with "
         f"random.Random({SHORTLIST_SEED}) (not Random(43)); classes in order POSITIVE, NEUTRAL, NEGATIVE.", ""]
for c in h.LABELS:
    pool = sorted([r for r in train if r["reference_label"] == c and eligible(r)], key=lambda r: r["filtered_index"])
    lines.append(f"## {c} (eligible pool {len(pool)})")
    for r in rng.sample(pool, 6):
        lines.append(f"- id {r['filtered_index']} | rating {r['rating']} | title: {r['title']!r}")
        lines.append(f"  text: {r['text']!r}")
    lines.append("")
open("evidence/phase2_fewshot_shortlist.md", "w", encoding="utf-8").write("\n".join(lines))
print(f"wrote shortlist ({len(lines)} lines)")

tok = AutoTokenizer.from_pretrained(TEMPLATE_REPO)
rng2 = random.Random(DISPLAY_SEED)
picks = []
for c, k in zip(h.LABELS, (7, 7, 6)):
    picks += rng2.sample([r for r in train if r["reference_label"] == c], k)
rng2.shuffle(picks)
out = [f"# 20 rendered training examples (TRAIN rows only)",
       f"Template source: {TEMPLATE_REPO} (provisional prompt wording, D-01/D-02 open). Rows drawn with "
       f"random.Random({DISPLAY_SEED}) (7 POSITIVE, 7 NEUTRAL, 6 NEGATIVE, then shuffled). Exact string handed to the tokenizer, with ids and ratings for you to compare.", ""]
for r in picks:
    m = h.build_messages_fine_tuned(r["title"], r["text"], target=r["reference_label"])
    s = tok.apply_chat_template(m, tokenize=False)
    out.append(f"## id {r['filtered_index']} | rating {r['rating']} | label {r['reference_label']}")
    out.append("```")
    out.append(s)
    out.append("```")
    out.append("")
open("evidence/phase2_training_examples_20.md", "w", encoding="utf-8").write("\n".join(out))
print("wrote 20 examples; classes:", {c: sum(r["reference_label"] == c for r in picks) for c in h.LABELS})
