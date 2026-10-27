# Source of build/a4_finetune.ipynb. Cell format: "# %% [SECTION] title" for code, "# %% [markdown]" for text.
# The helper module src/a4_helpers.py is inlined by tools/build_notebook.py as the first code cell.
# Never hand-edit the generated notebook.

# %% [markdown]
# # MBAX 6418 Assignment 4: Fine-Tuning, three approaches on Amazon Gift Cards reviews
# Zero-shot and few-shot on the hosted model, and a QLoRA fine-tune of a small model, all on the same 300 test reviews.
# Sections: S0 setup, S1 data, S2 prompts, S3 freeze check, S4 hosted predictions, S5 fine-tuning,
# S6 saved-adapter inference, S7 pre-scoring checks, S8 RESULTS (reads saved files only), S9 consistency, S10 report.

# %% [S0] CONFIG, versions, GPU, secrets
import importlib.metadata as _md
import json, math, os, subprocess, sys, time

MODE = "final"  # "dryrun": plumbing on TRAIN rows only, never the test set. "final": the single full run.
USE_DRIVE = True  # final run: True, to copy artifacts to Google Drive after each long step

OUT = "/content/a4_out"
CACHE_DIR = OUT + "/hosted_cache"
os.makedirs(OUT, exist_ok=True)

CONFIG = {
    "prompt": {"system": SYSTEM_PROMPT, "instruction": USER_INSTRUCTION},
    "hosted": {"base_url": "http://dobolyi.com:9001/v1", "model": "cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit",
               "temperature": 0, "max_tokens": 8, "extra_body": {"chat_template_kwargs": {"enable_thinking": False}},
               "timeout_s": 120, "max_retries": 3, "retry_backoff_s": 2},
    "fewshot_ids": [13547, 16202, 11866, 2749, 9272, 9440],
    # D-05 re-decided (DEC-11): Gemma 3 4B. google/gemma-3-4b-it is gated, so the ungated Unsloth copy of the same
    # weights is loaded and quantized to 4-bit on load (the recorded base id will be this copy, see DEC-12).
    "small_model": {"load_id": "unsloth/gemma-3-4b-it", "load_in_4bit": True, "max_seq_length": 512,
                    "max_new_tokens": 8, "batch_size": 1, "do_sample": False, "skip_special_tokens": True,
                    "instruction_part": "<start_of_turn>user\n", "response_part": "<start_of_turn>model\n",
                    "strip_bos_from_text": True,
                    # C-28: hub revisions seen in the dry run (2026-10-26); the run stops if either changed.
                    "expected_revisions": {"unsloth/gemma-3-4b-it": "bf46152c47f5dd20b896357cb51abc4c03b8ee8c",
                                           "unsloth/gemma-3-4b-it-unsloth-bnb-4bit": "316726ca0bd24aa323bfaf86e8a379ee1176d1fe"},
                    # DEC-12 (pending): id that must appear in adapter_config.json. adapter_base_id_override None keeps
                    # what Unsloth writes; a string rewrites the field openly (printed) before the ZIP is built.
                    "adapter_base_id_override": None,
                    "expected_adapter_base_id": "unsloth/gemma-3-4b-it-unsloth-bnb-4bit"},
    "train": {"r": 16, "lora_alpha": 16, "lora_dropout": 0, "bias": "none",
              "finetune_vision_layers": False, "finetune_language_layers": True,
              "finetune_attention_modules": True, "finetune_mlp_modules": True,
              "expected_lora_modules": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
              "learning_rate": 2e-4, "weight_decay": 0.01, "lr_scheduler_type": "linear", "warmup_steps": 5,
              "per_device_train_batch_size": 2, "gradient_accumulation_steps": 8, "num_train_epochs": 2,
              "optim": "adamw_8bit", "seed": 3407, "use_gradient_checkpointing": "unsloth", "packing": False},
    # DEC-05 (a plus b): hosted flip rate on TRAIN reviews only, separate from the reported results.
    "flip_rate": {"seed": 20261029, "per_class": 10, "repeats": 3, "approaches": ["zero_shot", "few_shot"]},
}
SM = CONFIG["small_model"]
TR = CONFIG["train"]
FROZEN_KEYS = ["prompt", "hosted", "fewshot_ids", "small_model", "train", "flip_rate"]
# Run-specific values are NOT frozen (they differ between dry run and final run).
# flip_items_per_class: the dry run sends 1 review per class (18 calls) to test plumbing; the final run sends all 30.
RUN = {"mode": MODE, "smoke_max_steps": 10 if MODE == "dryrun" else -1, "workers": 4,
       "flip_items_per_class": 1 if MODE == "dryrun" else CONFIG["flip_rate"]["per_class"]}
APPROVED_FREEZE_HASH = "8a1f06f40c4f3f273bd8149f7b4c25a9c0b20005ae5b5b435ae51be7a0e9e111"  # "FREEZE APPROVED 8a1f06f4", 2026-10-26

PACKAGES = ["torch", "transformers", "peft", "accelerate", "datasets", "trl", "bitsandbytes", "unsloth", "unsloth_zoo",
            "openai", "requests", "scikit-learn", "scipy", "statsmodels", "pandas", "numpy", "matplotlib", "safetensors"]


def package_versions():
    v = {"python": sys.version.split()[0]}
    for p in PACKAGES:
        try:
            v[p] = _md.version(p)
        except _md.PackageNotFoundError:
            v[p] = "not installed"
    return v


VERSIONS_S0 = package_versions()
print("MODE:", MODE, "| config keys:", list(CONFIG))
print("versions:", VERSIONS_S0)
gpu = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
                     capture_output=True, text=True)
GPU_REPORT = gpu.stdout.strip() if gpu.returncode == 0 else "no GPU (nvidia-smi failed)"
print("GPU:", GPU_REPORT)

try:
    from google.colab import userdata
    API_KEY = userdata.get("CLASS_API_KEY")
except Exception:
    API_KEY = os.environ.get("CLASS_API_KEY")
assert API_KEY, "CLASS_API_KEY not found in Colab Secrets or environment"
print("class API key loaded:", True)  # the value is never printed or written

if USE_DRIVE:
    from google.colab import drive
    drive.mount("/content/drive")
    DRIVE_DIR = "/content/drive/MyDrive/a4_out"
    os.makedirs(DRIVE_DIR, exist_ok=True)
    CACHE_DIR = DRIVE_DIR + "/hosted_cache"  # survives a runtime restart; the first response per prompt stays the answer


def persist(*paths):
    """Copy artifacts to Drive when mounted (runtime storage is temporary)."""
    if not USE_DRIVE:
        return
    import shutil
    for p in paths:
        shutil.copy(p, DRIVE_DIR)


# %% [S1] Data: rebuild the splits from the raw file and cross-check against split_data.zip
import hashlib, urllib.request

RAW_URL = "https://mcauleylab.ucsd.edu/public_datasets/data/amazon_2023/raw/review_categories/Gift_Cards.jsonl.gz"
RAW_PATH = "/content/Gift_Cards.jsonl.gz"
ZIP_PATH = "/content/split_data.zip"
EXPECTED_ZIP_SHA256 = "1e827e0f1d0dd673c677c2db9a3b81e4b5fb9d011ca3585a68423735044fa699"
if not os.path.exists(RAW_PATH):
    urllib.request.urlretrieve(RAW_URL, RAW_PATH)


def file_sha256(path):
    d = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            d.update(chunk)
    return d.hexdigest()


raw_lines = list(read_gz_lines(RAW_PATH))
print("C-01 raw file: size", os.path.getsize(RAW_PATH), "sha256", file_sha256(RAW_PATH), "physical lines", len(raw_lines))
assert len(raw_lines) > 0
assert file_sha256(ZIP_PATH) == EXPECTED_ZIP_SHA256, "split_data.zip is not the expected file"
survivors = list(iter_survivors(raw_lines))
splits = build_splits(survivors)
zipped = read_zip_splits(ZIP_PATH)
DATA_CHECKS = run_data_checks(survivors, splits, zipped)
for r in DATA_CHECKS:
    print(r["id"], "PASS" if r["pass"] else "FAIL", "|", r["detail"][:160])
with open(OUT + "/s1_data_checks.json", "w") as f:
    json.dump(DATA_CHECKS, f, indent=1)

# Seal: after this cell only the training rows keep labels. The evaluation rows carry title and text only;
# their reference labels are held in SEALED_TEST_LABELS and read only by S8. The reserved set is never loaded again.
TRAIN = splits["train"]
TRAIN_BY_ID = {r["filtered_index"]: r for r in TRAIN}
TEST = [{"original_row": r["original_row"], "filtered_index": r["filtered_index"], "title": r["title"], "text": r["text"]}
        for r in splits["test"]]
SEALED_TEST_LABELS = {r["filtered_index"]: r["reference_label"] for r in splits["test"]}
RESERVED_IDS = {r["filtered_index"] for r in splits["val"]} | {r["filtered_index"] for r in splits["test"]}
N_TRAIN = len(TRAIN)
del splits, zipped, survivors, raw_lines
print("sealed. train rows:", N_TRAIN, "| test rows (inputs only):", len(TEST), "| reserved ids:", len(RESERVED_IDS))

# %% [S2] Prompts: complete prompts for one review under all three approaches, plus checks C-12, C-14, C-14b, C-15
FEWSHOT_IDS = CONFIG["fewshot_ids"]
FEWSHOT = fewshot_examples(TRAIN_BY_ID, FEWSHOT_IDS)

if MODE == "final":
    EVAL_ITEMS = TEST
else:
    # Dry run: 3 per class from TRAIN (not few-shot), first by filtered_index. Plumbing only, no accuracy decisions.
    _picked = []
    for _c in LABELS:
        _rows = sorted([r for r in TRAIN if r["reference_label"] == _c and r["filtered_index"] not in FEWSHOT_IDS],
                       key=lambda r: r["filtered_index"])[:3]
        _picked += _rows
    EVAL_ITEMS = [{"original_row": r["original_row"], "filtered_index": r["filtered_index"], "title": r["title"],
                   "text": r["text"]} for r in sorted(_picked, key=lambda r: r["filtered_index"])]
EVAL_IDS = [e["filtered_index"] for e in EVAL_ITEMS]
print("evaluation items:", len(EVAL_ITEMS), "| mode:", MODE)

FLIP = CONFIG["flip_rate"]
FLIP_IDS = flip_sample(TRAIN, FEWSHOT_IDS, FLIP["per_class"], FLIP["seed"])
assert set(FLIP_IDS) <= set(TRAIN_BY_ID) and not set(FLIP_IDS) & (RESERVED_IDS | set(FEWSHOT_IDS))
print(f"DEC-05 flip sample: {len(FLIP_IDS)} TRAIN ids, none few-shot or reserved, seed {FLIP['seed']}:", FLIP_IDS)


def zero_shot_messages(item):
    return build_messages_zero_shot(item["title"], item["text"])


def few_shot_messages(item):
    return build_messages_few_shot(item["title"], item["text"], FEWSHOT)


def fine_tuned_messages(item):
    return build_messages_fine_tuned(item["title"], item["text"])


_demo = EVAL_ITEMS[0]
print("Same review under all three approaches: filtered_index", _demo["filtered_index"])
for _name, _fn in (("ZERO-SHOT", zero_shot_messages), ("FEW-SHOT", few_shot_messages), ("FINE-TUNED (inference prompt)", fine_tuned_messages)):
    print("\n=====", _name, "=====")
    for _m in _fn(_demo):
        print(f"[{_m['role']}]\n{_m['content']}\n")

check_fewshot(FEWSHOT_IDS, set(TRAIN_BY_ID), RESERVED_IDS, few_shot_messages(_demo), TRAIN_BY_ID)
print("C-12 PASS: few-shot ids are train rows, disjoint from reserved ids, and match the prompt turns")
_rec = dict(TRAIN[0])
_alt = dict(_rec, rating=1.0 if _rec["rating"] != 1.0 else 5.0, reference_label="NEGATIVE" if _rec["reference_label"] != "NEGATIVE" else "POSITIVE")
assert build_messages_zero_shot(_rec["title"], _rec["text"]) == build_messages_zero_shot(_alt["title"], _alt["text"])
assert zero_shot_messages(_rec) == zero_shot_messages(_alt)
print("C-14 PASS: prompts identical when rating and reference_label are altered")
check_instruction_identity(zero_shot_messages(_demo), few_shot_messages(_demo), fine_tuned_messages(_demo))
INSTRUCTION_HASH = instruction_hash(zero_shot_messages(_demo))
print("C-14b PASS: instruction hash", INSTRUCTION_HASH[:16])
for _e in EVAL_ITEMS:
    check_prompt_inputs(_e, zero_shot_messages(_e))
    assert set(_e.keys()) == {"original_row", "filtered_index", "title", "text"}
print("C-15 PASS: every built prompt is a function of title and text only; evaluation items carry no other fields")

# %% [S3] FREEZE CHECK
CANONICAL_PROMPTS = canonical_prompt_fingerprint(FEWSHOT)  # rendered prompts and parser table: helper drift changes the hash
FROZEN_HASH = frozen_hash(dict(CONFIG, instruction_hash=INSTRUCTION_HASH, canonical_prompts=CANONICAL_PROMPTS, flip_ids=FLIP_IDS),
                          FROZEN_KEYS + ["instruction_hash", "canonical_prompts", "flip_ids"])
print("frozen config hash:", FROZEN_HASH)
if MODE == "final":
    assert APPROVED_FREEZE_HASH and len(APPROVED_FREEZE_HASH) >= 8 and FROZEN_HASH.startswith(APPROVED_FREEZE_HASH), "C-26: hash differs from the approved hash"
    print("C-26 PASS: frozen hash matches the approved hash")
else:
    print("dry run: nothing is frozen yet")

# %% [S4] Hosted predictions (zero-shot and few-shot). Raw responses are saved verbatim.
from concurrent.futures import ThreadPoolExecutor

HOSTED = CONFIG["hosted"]


def run_hosted(approach, build):
    t0 = time.perf_counter()

    def one(item):
        msgs = build(item)
        rec = call_hosted(msgs, HOSTED, API_KEY, CACHE_DIR, FROZEN_HASH)
        return {"filtered_index": item["filtered_index"], "original_row": item["original_row"], "title": item["title"],
                "text": item["text"], "messages": msgs, "raw_response": rec["content"], "prediction": rec["prediction"],
                "finish_reason": rec["finish_reason"], "completion_tokens": rec["completion_tokens"],
                "violations": rec["violations"], "latency_s": rec["latency_s"], "attempts": rec["attempts"],
                "from_cache": rec["from_cache"], "response_json": rec["raw"]}

    with ThreadPoolExecutor(max_workers=RUN["workers"]) as ex:
        recs = list(ex.map(one, EVAL_ITEMS))
    recs.sort(key=lambda r: r["filtered_index"])
    wall = time.perf_counter() - t0
    path = f"{OUT}/hosted_{approach}_raw.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    persist(path)
    n_inv = sum(r["prediction"] == "INVALID" for r in recs)
    n_viol = sum(bool(r["violations"]) for r in recs)
    print(f"{approach}: {len(recs)} items, INVALID {n_inv}, calls with violations {n_viol}, cache hits "
          f"{sum(r['from_cache'] for r in recs)}, wall {wall:.1f}s, sum latency {sum(r['latency_s'] for r in recs):.1f}s")
    return recs, {"wall_s": wall, "calls": len(recs), "invalid": n_inv, "violations": n_viol}


HOSTED_ZERO, HOSTED_ZERO_COST = run_hosted("zero_shot", zero_shot_messages)
HOSTED_FEW, HOSTED_FEW_COST = run_hosted("few_shot", few_shot_messages)

# %% [S4b] DEC-05 hosted flip rate on TRAIN prompts (separate measurement; not used for any prediction or setting)
# Each prompt is sent 3 times, back to back, so this measures short-term repeatability within one run, not the
# variation between separate runs. Each repeat has its own cache folder (separate requests); the folder name includes
# MODE so dry-run answers are never reused in the final run. A restart resumes from saved answers instead of re-rolling;
# prompts whose repeats came from different kernel sessions are listed as mixed_session_ids.
# No evaluation labels are read here (TRAIN labels only pick the dry-run subset); correctness is not measured.
FLIP_BUILDERS = {"zero_shot": zero_shot_messages, "few_shot": few_shot_messages}
_flip_run = []
for _c in LABELS:
    _flip_run += [i for i in FLIP_IDS if TRAIN_BY_ID[i]["reference_label"] == _c][:RUN["flip_items_per_class"]]
FLIP_RUN_IDS = sorted(_flip_run)
del _flip_run
if MODE == "final":
    assert FLIP_RUN_IDS == FLIP_IDS, "final run must send the whole frozen flip sample"
FLIP_ITEMS = {i: {"title": TRAIN_BY_ID[i]["title"], "text": TRAIN_BY_ID[i]["text"]} for i in FLIP_RUN_IDS}


def _flip_one(job):
    approach, i = job
    recs = repeat_hosted(FLIP_BUILDERS[approach](FLIP_ITEMS[i]), HOSTED, API_KEY, f"{CACHE_DIR}/flip_{MODE}_{approach}",
                         FROZEN_HASH, FLIP["repeats"])
    return [{"approach": approach, "filtered_index": i, "repeat": k + 1, "raw_response": r["content"],
             "prediction": r["prediction"], "finish_reason": r["finish_reason"], "violations": r["violations"],
             "latency_s": r["latency_s"], "from_cache": r["from_cache"], "session_id": r["session_id"],
             "created_utc": r["created_utc"]} for k, r in enumerate(recs)]


_t0 = time.perf_counter()
with ThreadPoolExecutor(max_workers=RUN["workers"]) as ex:
    _flip_raw = [r for rs in ex.map(_flip_one, [(a, i) for a in FLIP["approaches"] for i in FLIP_RUN_IDS]) for r in rs]
print(f"S4b wall {time.perf_counter() - _t0:.1f}s (cache reads included)")
FLIP_PATH = OUT + "/hosted_flip_rate_raw.jsonl"
with open(FLIP_PATH, "w", encoding="utf-8") as f:
    for r in _flip_raw:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
persist(FLIP_PATH)
for _a, _v in flip_summary(_flip_raw, FLIP["approaches"]).items():
    print(f"{_a}: {_v['items']} TRAIN prompts x {_v['repeats']} calls | label flips {_v['label_flips']} ids {_v['label_flip_ids']} | "
          f"raw-text flips {_v['raw_flips']} | INVALID responses {_v['invalid_responses']} | calls with violations "
          f"{_v['calls_with_violations']} | cache hits {_v['cache_hits']} | mixed-session prompts {_v['mixed_session_ids']}")

# %% [S5a] Fine-tuning: install Unsloth stack (recipe from the Unsloth Colab notebook, versions recorded below)
def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print("$", cmd[:110], "-> rc", r.returncode)
    if r.returncode != 0:
        print((r.stdout + r.stderr)[-1500:])
        raise RuntimeError("install step failed: " + cmd[:60])


try:
    import unsloth  # noqa: F401
    print("unsloth already importable")
except Exception:
    sh('pip install -q sentencepiece protobuf "datasets==4.3.0" "huggingface_hub>=0.34.0" hf_transfer')
    sh("pip install -q --no-deps unsloth_zoo==2026.10.9 bitsandbytes==0.50.2 accelerate==1.15.0 peft==0.21.2 trl triton unsloth==2026.10.9")
    sh("unsloth install-kernels")
    sh('pip install -q --no-deps --upgrade "torchao>=0.16.0"')
    sh("pip install -q transformers==4.57.6")
    sh("pip install -q --no-deps trl==0.22.2")
VERSIONS_S5 = package_versions()
print("versions after install:", VERSIONS_S5)

# %% [S5b] Fine-tuning: prepared-record checks C-11 and C-16 (before any training)
from unsloth import FastModel  # must be imported before transformers and trl
import gc, torch
from transformers import AutoTokenizer

TRAIN_EXAMPLES = [{"filtered_index": r["filtered_index"],
                   "messages": build_messages_fine_tuned(r["title"], r["text"], target=r["reference_label"])} for r in TRAIN]
COUNTS = check_training_examples(TRAIN_EXAMPLES, TRAIN, per_class=TRAIN_PER_CLASS)
print("C-11 PASS: the objects handed to the trainer are exactly the 900 prescribed rows", COUNTS)

from huggingface_hub import HfApi
_revs = {rid: HfApi().model_info(rid).sha for rid in SM["expected_revisions"]}
print("hub revisions:", _revs)
assert _revs == SM["expected_revisions"], f"C-28: a hub revision changed: {_revs}"
print("C-28 PASS: the model repositories are at the revisions recorded in CONFIG")
HUB_TOKENIZER = AutoTokenizer.from_pretrained(SM["load_id"])
HUB_TEMPLATE_HASH = sha256_hex(HUB_TOKENIZER.chat_template)


def render_train_text(tok_, messages):
    """The template emits BOS as text and the tokenizer adds BOS again, so the text drops the leading BOS (same as the
    Unsloth Gemma 3 notebook); checks C-11c (train) and C-29 (inference prefix) prove a single BOS remains."""
    return render_chat_text(tok_, messages, SM["strip_bos_from_text"])


TRAIN_TEXTS = [render_train_text(HUB_TOKENIZER, e["messages"]) for e in TRAIN_EXAMPLES]
TRAIN_LENGTHS = [len(HUB_TOKENIZER(t)["input_ids"]) for t in TRAIN_TEXTS]  # with the BOS the tokenizer adds
check_no_truncation(TRAIN_LENGTHS, SM["max_seq_length"])
print("C-16 PASS (train): longest example", max(TRAIN_LENGTHS), "tokens <= max_seq_length", SM["max_seq_length"])
def _ids_of(enc):
    return enc["input_ids"] if hasattr(enc, "keys") else enc


_lens_eval = [len(_ids_of(HUB_TOKENIZER.apply_chat_template(fine_tuned_messages(e), tokenize=True, add_generation_prompt=True)))
              for e in EVAL_ITEMS]
check_no_truncation([n + SM["max_new_tokens"] for n in _lens_eval], SM["max_seq_length"])
print("C-16 PASS (inference prompts + max_new_tokens): longest", max(_lens_eval), "prompt tokens")
print("example rendered training text:\n" + TRAIN_TEXTS[0][:600])

# %% [S5c] Fine-tuning: load, LoRA, mask, train, save the adapter, build and verify the ZIP
from datasets import Dataset
from transformers import DataCollatorForSeq2Seq
from trl import SFTConfig, SFTTrainer
from unsloth.chat_templates import train_on_responses_only

torch.cuda.reset_peak_memory_stats()
model, tokenizer = FastModel.from_pretrained(model_name=SM["load_id"], max_seq_length=SM["max_seq_length"],
                                             load_in_4bit=SM["load_in_4bit"], load_in_8bit=False, full_finetuning=False)
text_tok = getattr(tokenizer, "tokenizer", tokenizer)  # Gemma 3 may come back as a processor; text work uses its tokenizer
print("loaded tokenizer object:", type(tokenizer).__name__, "| text tokenizer:", type(text_tok).__name__)
TEMPLATE_HASH_TRAIN = sha256_hex(text_tok.chat_template)
TEMPLATE_MATCHES_ORIGINAL = TEMPLATE_HASH_TRAIN == HUB_TEMPLATE_HASH
print("chat template hash (train):", TEMPLATE_HASH_TRAIN[:16], "| equals the hub tokenizer of the load id:", TEMPLATE_MATCHES_ORIGINAL)
print("loaded tokenizer eos/pad/bos:", text_tok.eos_token, text_tok.pad_token, text_tok.bos_token, "| hub tokenizer eos/pad/bos:",
      HUB_TOKENIZER.eos_token, HUB_TOKENIZER.pad_token, HUB_TOKENIZER.bos_token, "| differences are recorded, not hidden")
# The training text is rendered with the tokenizer that is actually loaded (the one used again at inference), and
# the truncation check is repeated on it.
TRAIN_TEXTS = [render_train_text(text_tok, e["messages"]) for e in TRAIN_EXAMPLES]
TRAIN_LENGTHS = [len(text_tok(t)["input_ids"]) for t in TRAIN_TEXTS]
check_no_truncation(TRAIN_LENGTHS, SM["max_seq_length"])
print("C-16 PASS (loaded tokenizer): longest training example", max(TRAIN_LENGTHS), "tokens")
print("rendered tail of one example:", repr(TRAIN_TEXTS[0][-60:]))
model = FastModel.get_peft_model(
    model, finetune_vision_layers=TR["finetune_vision_layers"], finetune_language_layers=TR["finetune_language_layers"],
    finetune_attention_modules=TR["finetune_attention_modules"], finetune_mlp_modules=TR["finetune_mlp_modules"],
    r=TR["r"], lora_alpha=TR["lora_alpha"], lora_dropout=TR["lora_dropout"], bias=TR["bias"],
    use_gradient_checkpointing=TR["use_gradient_checkpointing"], random_state=TR["seed"], use_rslora=False, loftq_config=None)
def count_params(m):
    """4-bit weights are stored packed (two per element), so a plain numel undercounts them by half."""
    trainable = total = 0
    for p in m.parameters():
        n = p.numel() * (2 if p.__class__.__name__ == "Params4bit" else 1)
        total += n
        if p.requires_grad:
            trainable += n
    return trainable, total


TRAINABLE, TOTAL = count_params(model)
_lora_names = [n for n, _ in model.named_modules() if n.endswith(".lora_A.default")]
LORA_MODULE_TYPES = sorted({n.split(".lora_A")[0].split(".")[-1] for n in _lora_names})
_cfg = getattr(model.config, "text_config", model.config)
N_LAYERS = _cfg.num_hidden_layers
print(f"trainable parameters {TRAINABLE:,} of {TOTAL:,} (4-bit weights counted unpacked)")
print("LoRA attached to module types:", LORA_MODULE_TYPES, "| adapted modules:", len(_lora_names), "| decoder layers:", N_LAYERS)
assert set(LORA_MODULE_TYPES) == set(TR["expected_lora_modules"]), f"C-27: LoRA module types {LORA_MODULE_TYPES} differ from the expected ones"
assert len(_lora_names) == len(TR["expected_lora_modules"]) * N_LAYERS, f"C-27: {len(_lora_names)} adapted modules, expected {len(TR['expected_lora_modules']) * N_LAYERS}"
assert not any("vision" in n for n in _lora_names), "C-27: a vision module was adapted"
print("C-27 PASS: all 7 projection types are adapted in every decoder layer; no vision module is adapted")

train_ds = Dataset.from_list([{"text": t} for t in TRAIN_TEXTS])
_args = dict(per_device_train_batch_size=TR["per_device_train_batch_size"],
             gradient_accumulation_steps=TR["gradient_accumulation_steps"], warmup_steps=TR["warmup_steps"],
             learning_rate=TR["learning_rate"], logging_steps=5, optim=TR["optim"], weight_decay=TR["weight_decay"],
             lr_scheduler_type=TR["lr_scheduler_type"], seed=TR["seed"], output_dir=OUT + "/trainer_out", report_to="none")
if RUN["smoke_max_steps"] > 0:
    _args["max_steps"] = RUN["smoke_max_steps"]  # dry run smoke only
else:
    _args["num_train_epochs"] = TR["num_train_epochs"]
trainer = SFTTrainer(model=model, tokenizer=tokenizer, train_dataset=train_ds, eval_dataset=None,
                     args=SFTConfig(dataset_text_field="text", packing=TR["packing"], max_length=SM["max_seq_length"], **_args))
trainer = train_on_responses_only(trainer, instruction_part=SM["instruction_part"], response_part=SM["response_part"])
print("trainer precision flags: fp16", trainer.args.fp16, "bf16", trainer.args.bf16, "| optim", trainer.args.optim)

# Prove the loss mask (DEC-02): the unmasked label tokens must decode to exactly the label plus the end-of-turn token.
for _i in range(40):
    _ex = trainer.train_dataset[_i]
    assert _ex["input_ids"][0] == text_tok.bos_token_id and _ex["input_ids"][1] != text_tok.bos_token_id, "C-11c: BOS is missing or doubled"
    _lab = [t for t in _ex["labels"] if t != -100]
    _dec = text_tok.decode(_lab)
    _want = TRAIN_EXAMPLES[_i]["messages"][-1]["content"]
    assert _dec.strip().startswith(_want) and len(_lab) <= 6, f"C-11b: mask wrong for example {_i}: {_dec!r}"
print("masking PASS on 40 examples: unmasked tokens decode to the label (+ end token). Example:", repr(_dec))

torch.cuda.reset_peak_memory_stats()
_t0 = time.perf_counter()
TRAIN_STATS = trainer.train()
TRAIN_SECONDS = time.perf_counter() - _t0
assert math.isfinite(TRAIN_STATS.training_loss), "training loss is not finite (fp16 overflow?)"
PEAK_VRAM_TRAIN_GB = torch.cuda.max_memory_allocated() / 1e9
print(f"training: own timer {TRAIN_SECONDS:.1f}s, trainer train_runtime {TRAIN_STATS.metrics.get('train_runtime')}, "
      f"steps {TRAIN_STATS.global_step}, final loss {TRAIN_STATS.training_loss:.4f}, peak VRAM {PEAK_VRAM_TRAIN_GB:.2f} GB")

import shutil, zipfile
ADAPTER_DIR = OUT + "/adapter_train_dir"
model.save_pretrained(ADAPTER_DIR)
print("files Unsloth wrote:", sorted(os.listdir(ADAPTER_DIR)))
_cfg_path = os.path.join(ADAPTER_DIR, "adapter_config.json")
with open(_cfg_path, encoding="utf-8") as _f:
    _cfg_written = json.load(_f)
BASE_ID_WRITTEN = _cfg_written.get("base_model_name_or_path")
if SM["adapter_base_id_override"]:
    _cfg_written["base_model_name_or_path"] = SM["adapter_base_id_override"]
    with open(_cfg_path, "w", encoding="utf-8") as _f:
        json.dump(_cfg_written, _f, indent=2)
    print("DEC-12: base_model_name_or_path rewritten from", BASE_ID_WRITTEN, "to", SM["adapter_base_id_override"])
ADAPTER_ZIP = OUT + "/adapter.zip"
build_adapter_zip([os.path.join(ADAPTER_DIR, n) for n in ADAPTER_FILES], ADAPTER_ZIP)
print("C-17 zip namelist:", verify_adapter_zip(ADAPTER_ZIP))
with zipfile.ZipFile(ADAPTER_ZIP) as _z:
    ADAPTER_CONFIG = json.loads(_z.read("adapter_config.json"))
print("adapter_config base_model_name_or_path:", ADAPTER_CONFIG.get("base_model_name_or_path"), "| written by Unsloth:", BASE_ID_WRITTEN)
assert ADAPTER_CONFIG.get("base_model_name_or_path") == SM["expected_adapter_base_id"], "C-17: adapter_config base id is not the frozen expected id"
print("C-17 PASS: ZIP has exactly the two files and the base id equals the frozen expected id")
ADAPTER_BYTES = os.path.getsize(ADAPTER_ZIP)
print("adapter.zip bytes:", ADAPTER_BYTES)
TRAIN_META = {"template_hash_train": TEMPLATE_HASH_TRAIN, "template_matches_hub": TEMPLATE_MATCHES_ORIGINAL, "n_layers": N_LAYERS,
              "trainable_params": TRAINABLE, "total_params": TOTAL, "lora_module_types": LORA_MODULE_TYPES,
              "train_seconds": TRAIN_SECONDS, "trainer_train_runtime": TRAIN_STATS.metrics.get("train_runtime"),
              "global_step": TRAIN_STATS.global_step, "training_loss": TRAIN_STATS.training_loss,
              "peak_vram_train_gb": PEAK_VRAM_TRAIN_GB, "adapter_zip_bytes": ADAPTER_BYTES,
              "adapter_base_id_written": BASE_ID_WRITTEN, "model_dtype": str(model.dtype),
              "fp16": trainer.args.fp16, "bf16": trainer.args.bf16, "hub_revisions": _revs, "versions_train": package_versions()}
with open(OUT + "/train_meta.json", "w") as _f:
    json.dump(TRAIN_META, _f, indent=1, default=str)
persist(ADAPTER_ZIP, OUT + "/train_meta.json")

# %% [S6a] Saved-adapter inference: fresh load from the extracted ZIP (no training objects survive)
from unsloth import FastModel
import gc, torch, shutil, zipfile
for _stale in range(1):  # free training objects when they exist; this section also runs after a runtime restart
    try:
        del trainer, train_ds
    except NameError:
        pass
    try:
        del model, tokenizer, text_tok
    except NameError:
        pass
gc.collect()
torch.cuda.empty_cache()
torch.cuda.reset_peak_memory_stats()
with open(OUT + "/train_meta.json") as _f:
    TRAIN_META = json.load(_f)
N_LAYERS = TRAIN_META["n_layers"]
TEMPLATE_HASH_TRAIN = TRAIN_META["template_hash_train"]
ADAPTER_ZIP = OUT + "/adapter.zip"
print("saved adapter:", verify_adapter_zip(ADAPTER_ZIP), os.path.getsize(ADAPTER_ZIP), "bytes")
with zipfile.ZipFile(ADAPTER_ZIP) as _z:
    ADAPTER_CONFIG = json.loads(_z.read("adapter_config.json"))

EXTRACT_DIR = OUT + "/adapter_extracted"
assert not os.path.exists(EXTRACT_DIR), "extract folder must be new"
with zipfile.ZipFile(ADAPTER_ZIP) as _z:
    _z.extractall(EXTRACT_DIR)
assert sorted(os.listdir(EXTRACT_DIR)) == sorted(ADAPTER_FILES)

from peft import PeftModel
base_model, tok_obj = FastModel.from_pretrained(model_name=SM["load_id"], max_seq_length=SM["max_seq_length"],
                                                load_in_4bit=SM["load_in_4bit"], load_in_8bit=False, full_finetuning=False)
tok = getattr(tok_obj, "tokenizer", tok_obj)
model = PeftModel.from_pretrained(base_model, EXTRACT_DIR)
FastModel.for_inference(model)
TEMPLATE_HASH_INFER = sha256_hex(tok.chat_template)
assert TEMPLATE_HASH_INFER == TEMPLATE_HASH_TRAIN, "C-18: chat template at inference differs from training"
print("C-18 PASS: fresh model instance, extracted adapter folder, template hash equal to training:", TEMPLATE_HASH_INFER[:16])
_r0 = TRAIN[0]
_full_ids = tok(render_chat_text(tok, build_messages_fine_tuned(_r0["title"], _r0["text"], target=_r0["reference_label"]),
                                 SM["strip_bos_from_text"]))["input_ids"]
_enc0 = tok.apply_chat_template(build_messages_fine_tuned(_r0["title"], _r0["text"]), tokenize=True, add_generation_prompt=True)
check_prompt_is_training_prefix(_enc0["input_ids"] if hasattr(_enc0, "keys") else _enc0, _full_ids)
print("C-29 PASS: the inference prompt tokens are exactly the start of the training tokens (single BOS)")
assert any("lora" in n for n, _ in model.named_parameters()), "no LoRA weights attached"
_n_loaded = sum(1 for n, _ in model.named_modules() if n.endswith(".lora_A.default"))
assert _n_loaded == len(TR["expected_lora_modules"]) * N_LAYERS, f"C-27: reloaded adapter has {_n_loaded} adapted modules"
print("C-27 PASS (reload): the extracted adapter attaches to", _n_loaded, "modules")


def classify_review(title, text):
    """The single inference procedure used for the 300 predictions and for the runnable example."""
    msgs = build_messages_fine_tuned(title, text)
    enc = tok.apply_chat_template(msgs, tokenize=True, add_generation_prompt=True, return_tensors="pt", return_dict=True)
    input_ids = enc["input_ids"].to("cuda")
    t0 = time.perf_counter()
    with torch.no_grad():
        out = model.generate(input_ids=input_ids, attention_mask=enc["attention_mask"].to("cuda"),
                             max_new_tokens=SM["max_new_tokens"], do_sample=SM["do_sample"], use_cache=True,
                             pad_token_id=tok.pad_token_id)
    new_tokens = out[0][input_ids.shape[1]:]
    raw = tok.decode(new_tokens, skip_special_tokens=SM["skip_special_tokens"])
    _eos = model.generation_config.eos_token_id
    _eos = set(_eos) if isinstance(_eos, (list, tuple)) else {_eos}
    return {"messages": msgs, "raw_response": raw, "prediction": parse_label(raw),
            "n_new_tokens": int(new_tokens.shape[0]), "latency_s": time.perf_counter() - t0,
            "ended_with_eos": any(int(t) in _eos for t in new_tokens)}


# %% [markdown]
# ## COMPLETE SAVED-ADAPTER INFERENCE EXAMPLE
# Loads the adapter extracted from the submitted ZIP, the exact base model and its tokenizer, applies the evaluation
# prompt and generation settings, and classifies one review from its title and text. No training code and no hosted calls.

# %% [S6b] COMPLETE SAVED-ADAPTER INFERENCE EXAMPLE
print("base model id:", SM["load_id"], "| tokenizer id:", SM["load_id"], "| adapter folder:", EXTRACT_DIR)
print("adapter_config base_model_name_or_path:", ADAPTER_CONFIG.get("base_model_name_or_path"))
print("package versions:", package_versions())
print("generation settings:", {k: SM[k] for k in ("max_new_tokens", "batch_size", "do_sample", "skip_special_tokens")},
      "| response processing: pred = raw.strip().upper(), accepted only if POSITIVE/NEUTRAL/NEGATIVE, else INVALID")
_ex_item = EVAL_ITEMS[0]
_ex_out = classify_review(_ex_item["title"], _ex_item["text"])
print("review (title):", _ex_item["title"])
print("messages passed to the chat template:")
for _m in _ex_out["messages"]:
    print(f"  [{_m['role']}] {_m['content'][:200]!r}")
print("raw response:", repr(_ex_out["raw_response"]), "| final label:", _ex_out["prediction"])

# %% [S6c] Saved-adapter inference: all evaluation predictions (raw file written here, labels not involved)
t0 = time.perf_counter()
FT_RAW = []
for _item in EVAL_ITEMS:
    _o = classify_review(_item["title"], _item["text"])
    FT_RAW.append({"filtered_index": _item["filtered_index"], "original_row": _item["original_row"], "title": _item["title"],
                   "text": _item["text"], "messages": _o["messages"], "raw_response": _o["raw_response"],
                   "prediction": _o["prediction"], "n_new_tokens": _o["n_new_tokens"], "ended_with_eos": _o["ended_with_eos"],
                   "latency_s": _o["latency_s"]})
FT_INFER_SECONDS = time.perf_counter() - t0
PEAK_VRAM_INFER_GB = torch.cuda.max_memory_allocated() / 1e9
FT_RAW_PATH = OUT + "/ft_raw.jsonl"
with open(FT_RAW_PATH, "w", encoding="utf-8") as f:
    for r in FT_RAW:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
persist(FT_RAW_PATH)
print(f"{len(FT_RAW)} predictions in {FT_INFER_SECONDS:.1f}s, INVALID {sum(r['prediction'] == 'INVALID' for r in FT_RAW)}, "
      f"not ended with EOS {sum(not r['ended_with_eos'] for r in FT_RAW)}, peak VRAM inference {PEAK_VRAM_INFER_GB:.2f} GB")

# %% [S7] Pre-scoring checks (C-13): exactly one prediction per evaluation id, for each approach
check_one_prediction_per_id({"zero_shot": HOSTED_ZERO, "few_shot": HOSTED_FEW, "fine_tuned": FT_RAW}, EVAL_IDS)
print("C-13 PASS: each approach has exactly one prediction for each of the", len(EVAL_IDS), "ids")

# %% [markdown]
# # S8 RESULTS
# Everything below reads saved files only. Reference labels are read here for the first time.

# %% [S8a] RESULTS: reference labels, submission files, checks C-19 and C-20
if MODE == "final":
    REF_BY_ID = dict(SEALED_TEST_LABELS)
else:
    REF_BY_ID = {i: TRAIN_BY_ID[i]["reference_label"] for i in EVAL_IDS}  # dry run: plumbing on train rows


def read_jsonl(path):
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


_ft_saved = read_jsonl(FT_RAW_PATH)
FT_RECORDS = [{"original_row": r["original_row"], "filtered_index": r["filtered_index"], "title": r["title"], "text": r["text"],
               "reference_label": REF_BY_ID[r["filtered_index"]], "prediction": r["prediction"], "raw_response": r["raw_response"]}
              for r in _ft_saved]
PRED_PATH = OUT + "/ft_test_predictions.jsonl"
write_predictions(PRED_PATH, FT_RECORDS)
check_predictions_records(read_predictions(PRED_PATH), EVAL_IDS)
print("C-19 PASS: predictions file has", len(FT_RECORDS), "rows, exact field order, ids equal the evaluation ids")

_first_per_class = {}
for r in sorted(_ft_saved, key=lambda r: r["filtered_index"]):
    _first_per_class.setdefault(REF_BY_ID[r["filtered_index"]], r)
PROMPT_EXAMPLES = [{"original_row": _first_per_class[c]["original_row"], "filtered_index": _first_per_class[c]["filtered_index"],
                    "reference_label": c, "messages": _first_per_class[c]["messages"]} for c in LABELS]
PROMPT_PATH = OUT + "/prompt_examples.jsonl"
with open(PROMPT_PATH, "w", encoding="utf-8", newline="\n") as f:
    for r in PROMPT_EXAMPLES:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
_expected = {r["filtered_index"]: fine_tuned_messages(next(e for e in EVAL_ITEMS if e["filtered_index"] == r["filtered_index"])) for r in PROMPT_EXAMPLES}
check_prompt_examples(read_jsonl(PROMPT_PATH), _expected)
print("C-20 PASS: 3 prompt examples, one per class, equal to the rebuilt prompts, no label inside messages")
persist(PRED_PATH, PROMPT_PATH)

# %% [S8b] RESULTS: metrics per approach (computed from the saved files)
import numpy as np
import pandas as pd

HOSTED_ZERO_FILE = read_jsonl(OUT + "/hosted_zero_shot_raw.jsonl")
HOSTED_FEW_FILE = read_jsonl(OUT + "/hosted_few_shot_raw.jsonl")
PREDS = {"zero_shot": {r["filtered_index"]: r["prediction"] for r in HOSTED_ZERO_FILE},
         "few_shot": {r["filtered_index"]: r["prediction"] for r in HOSTED_FEW_FILE},
         "fine_tuned": {r["filtered_index"]: r["prediction"] for r in read_predictions(PRED_PATH)}}
ORDER = sorted(REF_BY_ID)
METRICS = {n: compute_metrics([REF_BY_ID[i] for i in ORDER], [p[i] for i in ORDER]) for n, p in PREDS.items()}
rows = []
for n, m in METRICS.items():
    rows.append({"approach": n, "balanced_accuracy": round(m["balanced_accuracy"], 4), "macro_f1": round(m["macro_f1"], 4),
                 "correct": m["correct"], "incorrect": m["incorrect"], "INVALID": m["invalid"]})
print(pd.DataFrame(rows).to_string(index=False))
for n, m in METRICS.items():
    print(f"\n{n}: per class")
    print(pd.DataFrame(m["per_class"]).T.round(4).to_string())
# cross-check with scikit-learn on rows without INVALID predictions (sklearn mishandles prediction-only labels)
from sklearn.metrics import balanced_accuracy_score, f1_score
for n, p in PREDS.items():
    ok_ids = [i for i in ORDER if p[i] != "INVALID"]
    if ok_ids and len({REF_BY_ID[i] for i in ok_ids}) == 3:
        yt, yp = [REF_BY_ID[i] for i in ok_ids], [p[i] for i in ok_ids]
        m2 = compute_metrics(yt, yp)
        assert abs(m2["macro_f1"] - f1_score(yt, yp, average="macro", labels=LABELS)) < 1e-9
        assert abs(m2["balanced_accuracy"] - balanced_accuracy_score(yt, yp)) < 1e-9
print("\nscikit-learn cross-check PASS on the non-INVALID rows of each approach")
BEST = best_approach(METRICS)
print("highest macro-F1 approach (tie-break: balanced accuracy, then name):", BEST)

# %% [S8c] RESULTS: confusion matrices (rows reference, columns prediction, each row sums to 1)
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 3, figsize=(15, 4.5), sharey=True)
for ax, (n, m) in zip(axes, METRICS.items()):
    mat = np.array(normalize_rows(m["confusion"]))
    im = ax.imshow(mat, vmin=0, vmax=1, cmap="Blues")
    ax.set_title(n)
    ax.set_xticks(range(4)); ax.set_xticklabels(CM_COLUMNS, rotation=30)
    ax.set_yticks(range(3)); ax.set_yticklabels(LABELS)
    for i in range(3):
        for j in range(4):
            ax.text(j, i, f"{mat[i, j]:.2f}", ha="center", va="center", color="white" if mat[i, j] > 0.5 else "black")
fig.colorbar(im, ax=axes, fraction=0.02)
plt.savefig(OUT + "/confusion_three.png", dpi=120, bbox_inches="tight")
plt.show()
fig, ax = plt.subplots(figsize=(6.5, 5))
mat = np.array(normalize_rows(METRICS[BEST]["confusion"]))
ax.imshow(mat, vmin=0, vmax=1, cmap="Blues")
ax.set_title(f"{BEST} (highest macro-F1)")
ax.set_xticks(range(4)); ax.set_xticklabels(CM_COLUMNS); ax.set_yticks(range(3)); ax.set_yticklabels(LABELS)
for i in range(3):
    for j in range(4):
        ax.text(j, i, f"{mat[i, j]:.2f}", ha="center", va="center", color="white" if mat[i, j] > 0.5 else "black", fontsize=13)
plt.savefig(OUT + "/confusion_best.png", dpi=120, bbox_inches="tight")
plt.show()

# %% [S8d] RESULTS: exact McNemar tests, error analysis, cost view
MCNEMAR = pairwise_mcnemar(REF_BY_ID, PREDS)
for k, v in MCNEMAR.items():
    print(f"{k}: b={v['b']} c={v['c']} p={v['p']:.4f} (statsmodels {v['p_statsmodels']:.4f}, binomial cross-check {v['p_binomial']:.4f})")
print("Exact two-sided McNemar tests, three comparisons, no multiplicity adjustment applied.")
ERRORS = error_analysis(REF_BY_ID, PREDS["zero_shot"], PREDS["few_shot"], PREDS["fine_tuned"], n=10)
for k, v in ERRORS.items():
    print(k, "total", v["total"], "first ids", v["ids"])
COST = {"hosted_zero_shot": HOSTED_ZERO_COST, "hosted_few_shot": HOSTED_FEW_COST,
        "fine_tuned": {"train_seconds_own_timer": TRAIN_META["train_seconds"], "train_runtime_trainer": TRAIN_META["trainer_train_runtime"],
                       "peak_vram_train_gb": TRAIN_META["peak_vram_train_gb"], "peak_vram_infer_gb": PEAK_VRAM_INFER_GB,
                       "inference_seconds": FT_INFER_SECONDS, "adapter_zip_bytes": TRAIN_META["adapter_zip_bytes"]}}
print(json.dumps(COST, indent=1, default=str))

# %% [S8e] RESULTS: optional star-word title breakdown (descriptive only, approved in the G0 batch, never used to tune)
# Star-word title rule: the Phase 2 regex STAR_TITLE (for example "Five Stars", "Great 5 stars"). INVALID counts as wrong.
# The reference-label mix differs between the two groups, so the within-class table is the like-for-like comparison.
TITLE_BY_ID = {e["filtered_index"]: e["title"] for e in EVAL_ITEMS}
STAR_TITLES = star_title_breakdown(REF_BY_ID, TITLE_BY_ID, PREDS)
print(f"star-word titles: {STAR_TITLES['n_star']} of {STAR_TITLES['n_star'] + STAR_TITLES['n_rest']} | reference labels "
      f"{STAR_TITLES['star_label_mix']} (other titles {STAR_TITLES['rest_label_mix']})")
_fmt = lambda x: "n/a" if x is None else f"{x:.4f}"
print(pd.DataFrame([{"approach": n, "star_title_correct": v["star_correct"], "star_title_accuracy": _fmt(v["star_accuracy"]),
                     "other_correct": v["rest_correct"], "other_accuracy": _fmt(v["rest_accuracy"])}
                    for n, v in STAR_TITLES["by_approach"].items()]).to_string(index=False))
print("\nwithin each reference class (recall = correct / reviews of that class in the group):")
print(pd.DataFrame([{"approach": n, "class": c, "star_n": d["star_n"], "star_correct": d["star_correct"],
                     "star_recall": _fmt(d["star_recall"]), "other_n": d["rest_n"], "other_correct": d["rest_correct"],
                     "other_recall": _fmt(d["rest_recall"])}
                    for n, v in STAR_TITLES["by_approach"].items() for c, d in v["per_class"].items()]).to_string(index=False))

# %% [S9] Artifact consistency (C-19 to C-22): recompute from the saved files and compare with what was displayed
_re = read_predictions(PRED_PATH)
check_predictions_records(_re, EVAL_IDS)
_m2 = compute_metrics([r["reference_label"] for r in _re], [r["prediction"] for r in _re])
assert abs(_m2["macro_f1"] - METRICS["fine_tuned"]["macro_f1"]) < 1e-12 and abs(_m2["balanced_accuracy"] - METRICS["fine_tuned"]["balanced_accuracy"]) < 1e-12
assert _m2["confusion"] == METRICS["fine_tuned"]["confusion"]
print("C-21 PASS: fine-tuned metrics recomputed from the saved predictions file equal the displayed values")
for _n, _recs in (("zero_shot", HOSTED_ZERO_FILE), ("few_shot", HOSTED_FEW_FILE), ("fine_tuned", _re)):
    assert all(PREDS[_n][r["filtered_index"]] == parse_label(r["raw_response"]) for r in _recs)
print("predictions follow their raw responses for all three approaches")

# %% [S10] Report facts (generated from saved outputs; the prose below is written by the student)
FACTS = {
    "mode": MODE, "gpu": GPU_REPORT, "t4_tested_directly": "Tesla T4" in GPU_REPORT,
    "hosted_model": HOSTED["model"] + " (35B total, about 3B active)",
    "small_model": SM["load_id"], "trainable_params": TRAIN_META["trainable_params"], "total_params": TRAIN_META["total_params"],
    "lora_module_types": TRAIN_META["lora_module_types"], "model_dtype": TRAIN_META["model_dtype"],
    "fp16": TRAIN_META["fp16"], "bf16": TRAIN_META["bf16"], "hub_revisions": TRAIN_META["hub_revisions"],
    "training_settings": {k: TR[k] for k in TR}, "training_seconds": round(TRAIN_META["train_seconds"], 1),
    "generation_settings": {"hosted": {k: HOSTED[k] for k in ("temperature", "max_tokens", "extra_body")},
                            "fine_tuned": {k: SM[k] for k in ("max_new_tokens", "batch_size", "do_sample", "skip_special_tokens")}},
    "package_versions": package_versions(), "frozen_hash": FROZEN_HASH,
    "template_matches_hub": TRAIN_META["template_matches_hub"], "adapter_base_model_name_or_path": ADAPTER_CONFIG.get("base_model_name_or_path"),
    "metrics": {n: {"balanced_accuracy": m["balanced_accuracy"], "macro_f1": m["macro_f1"], "invalid": m["invalid"]} for n, m in METRICS.items()},
    "mcnemar": {k: {"b": v["b"], "c": v["c"], "p": v["p"]} for k, v in MCNEMAR.items()},
    # rebuilt from the saved file, so a restart before S10 cannot lose it; cost is the sum of per-call latencies
    "hosted_flip_rate_train": {"design": "3 back-to-back calls per TRAIN prompt in one run (short-term repeatability)",
                               "seed": FLIP["seed"], "repeats": FLIP["repeats"],
                               "by_approach": flip_summary(read_jsonl(OUT + "/hosted_flip_rate_raw.jsonl"), FLIP["approaches"])},
    "star_word_titles": {k: STAR_TITLES[k] for k in ("n_star", "n_rest", "star_label_mix", "rest_label_mix", "by_approach")},
}
print(json.dumps(FACTS, indent=1, default=str))
with open(OUT + "/report_facts.json", "w") as f:
    json.dump(FACTS, f, indent=1, default=str)
persist(OUT + "/report_facts.json")

# %% [markdown]
# # Report
# (Written by the student after reading the numbers above. The seven required topics: model, settings and few-shot choices;
# best approach with example errors; what the statistics support and their limits; training cost versus gain;
# one issue or decision investigated with the agent. Limits to check against the numbers: one dataset, one small model,
# one few-shot set, one run per approach, hosted model not the same size as the small model, star labels as noisy proxies,
# and whether titles such as "Five Stars" reveal the rating, which the optional title analysis can describe.)
