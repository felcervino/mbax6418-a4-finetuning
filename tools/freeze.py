"""Phase 4: compute the frozen config exactly as notebook cell S3 does, write frozen_config.json and its sha256.

CONFIG and FROZEN_KEYS are read from the S0 cell of notebook_src/a4_cells.py (not copied by hand), and the extra
frozen keys from the S3 cell. Only TRAIN rows are read (few-shot texts and the flip sample).
Usage: python tools/freeze.py [out_dir]
"""
import ast
import json
import os
import re
import sys
import zipfile

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.dirname(__file__))
import a4_helpers as h  # noqa: E402
from build_notebook import CELLS, parse_cells  # noqa: E402

ZIP = os.path.join(ROOT, "data", "split_data.zip")


def _cell(cells, tag):
    found = [c for c in cells if c["type"] == "code" and c["tag"] == tag]
    assert len(found) == 1, f"expected one {tag} cell, found {len(found)}"
    return found[0]["source"]


def read_config(cells_text):
    """CONFIG, FROZEN_KEYS, extra keys and APPROVED_FREEZE_HASH as the notebook defines them."""
    cells = parse_cells(cells_text)
    names = {"SYSTEM_PROMPT": h.SYSTEM_PROMPT, "USER_INSTRUCTION": h.USER_INSTRUCTION, "__builtins__": {}}
    found = {}
    for node in ast.parse(_cell(cells, "S0")).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) \
                and node.targets[0].id in ("CONFIG", "FROZEN_KEYS", "APPROVED_FREEZE_HASH"):
            found[node.targets[0].id] = eval(compile(ast.Expression(node.value), "S0", "eval"), dict(names))
    assert set(found) == {"CONFIG", "FROZEN_KEYS", "APPROVED_FREEZE_HASH"}, f"S0 is missing {set(found) ^ {'CONFIG', 'FROZEN_KEYS', 'APPROVED_FREEZE_HASH'}}"
    m = re.search(r"FROZEN_KEYS \+ (\[[^\]]*\])", _cell(cells, "S3"))
    assert m, "S3 no longer adds extra keys to FROZEN_KEYS in the expected form"
    return found["CONFIG"], found["FROZEN_KEYS"], ast.literal_eval(m.group(1)), found["APPROVED_FREEZE_HASH"]


def read_train(zip_path=ZIP):
    with zipfile.ZipFile(zip_path) as z:
        return [json.loads(x) for x in z.read("train.jsonl").decode("utf-8").split("\n") if x.strip()]


def compute(cfg, frozen_keys, extra_keys, train):
    unknown = set(extra_keys) - {"instruction_hash", "canonical_prompts", "flip_ids"}
    assert not unknown, f"freeze.py does not know how to compute {unknown}; update it to match S3"
    train_by_id = {r["filtered_index"]: r for r in train}
    fewshot = h.fewshot_examples(train_by_id, cfg["fewshot_ids"])
    flip = cfg["flip_rate"]
    extras = {"instruction_hash": h.instruction_hash(h.build_messages_zero_shot("t", "x")),  # item-independent
              "canonical_prompts": h.canonical_prompt_fingerprint(fewshot),
              "flip_ids": h.flip_sample(train, cfg["fewshot_ids"], flip["per_class"], flip["seed"])}
    obj = {k: cfg[k] for k in frozen_keys}
    obj.update({k: extras[k] for k in extra_keys})
    full = h.frozen_hash(dict(cfg, **extras), frozen_keys + list(extra_keys))
    assert full == h.config_hash(obj)
    return obj, full


def main(out_dir):
    with open(CELLS, encoding="utf-8") as f:
        cfg, keys, extra, approved = read_config(f.read())
    obj, full = compute(cfg, keys, extra, read_train())
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "frozen_config.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=1, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    with open(os.path.join(out_dir, "frozen_config.sha256"), "w", encoding="utf-8", newline="\n") as f:
        f.write(f"{full}  sha256 of canonical_json(frozen_config.json), equal to the notebook S3 FROZEN_HASH\n")
    print("frozen keys:", keys + extra)
    print("FROZEN_HASH:", full, "| first 8:", full[:8])
    print("APPROVED_FREEZE_HASH in S0:", approved)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ROOT)
