"""Phase 0 endpoint probe and DEC-03 (thinking off) investigation.

Reads ONLY train.jsonl from data/split_data.zip. Prompts use title and text only.
Key comes from env CLASS_API_KEY and is never printed or written.
Writes raw responses to evidence/phase0_endpoint_probe_<where>.jsonl.
Usage: python -I tools/probe_endpoint.py <where> <n_reviews>
"""
import hashlib
import json
import os
import sys
import time
import urllib.request
import zipfile

BASE_URL = "http://dobolyi.com:9001/v1"
MODEL = "cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit"
SYSTEM = "You are an expert product review analyst. Determine the sentiment each Amazon review expresses."
INSTRUCTION = ("Classify the sentiment of the review below as exactly one of: POSITIVE, NEUTRAL, NEGATIVE. "
               "Reply with exactly one word, no explanation.")

# Conditions probed. Prompt wording is the PLAN.md 4.2 default and is NOT a decision (D-01 is Phase 2).
CONDITIONS = {
    "default_thinking": {"max_tokens": 400, "extra": {}},
    "thinking_off": {"max_tokens": 50, "extra": {"chat_template_kwargs": {"enable_thinking": False}}},
}
N_DEFAULT = 2  # thinking-on calls are long, probe only a few


def key():
    k = os.environ.get("CLASS_API_KEY")
    if not k:
        raise SystemExit("CLASS_API_KEY not set")
    return k


def http(method, path, body=None):
    req = urllib.request.Request(BASE_URL + path, method=method,
                                 data=None if body is None else json.dumps(body).encode(),
                                 headers={"Authorization": "Bearer " + key(), "Content-Type": "application/json"})
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=180) as r:
        raw = r.read().decode()
    return raw, time.perf_counter() - t0


def messages(title, text):
    return [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"{INSTRUCTION}\n\nReview title: {title}\nReview text: {text}"}]


def main():
    where, n = sys.argv[1], int(sys.argv[2])
    out_path = f"evidence/phase0_endpoint_probe_{where}.jsonl"
    with zipfile.ZipFile("data/split_data.zip") as z, z.open("train.jsonl") as f:
        rows = [json.loads(line) for line in f.read().decode().splitlines()[:n]]

    raw_models, lat = http("GET", "/models")
    models = [m["id"] for m in json.loads(raw_models)["data"]]
    print(f"models: {models}  latency={lat:.2f}s")
    if MODEL not in models:
        raise SystemExit(f"FAIL: {MODEL} not served")

    with open(out_path, "w", encoding="utf-8") as out:
        out.write(json.dumps({"kind": "models", "raw": raw_models, "latency_s": lat}) + "\n")
        for cond, cfg in CONDITIONS.items():
            for i, r in enumerate(rows):
                if cond == "default_thinking" and i >= N_DEFAULT:
                    break
                msgs = messages(r["title"], r["text"])
                body = {"model": MODEL, "messages": msgs, "temperature": 0, "max_tokens": cfg["max_tokens"], **cfg["extra"]}
                raw, lat = http("POST", "/chat/completions", body)
                resp = json.loads(raw)
                msg = resp["choices"][0]["message"]
                reasoning = msg.get("reasoning") or msg.get("reasoning_content")
                content = msg.get("content")
                rec = {"kind": "chat", "condition": cond, "filtered_index": r["filtered_index"],
                       "request_body": body,
                       "messages_sha256": hashlib.sha256(json.dumps(msgs, sort_keys=True).encode()).hexdigest(),
                       "raw": raw, "latency_s": lat}
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                print(f"{cond:16s} idx={r['filtered_index']:>6} lat={lat:5.2f}s finish={resp['choices'][0].get('finish_reason')} "
                      f"usage={resp.get('usage', {}).get('completion_tokens')} "
                      f"reasoning_len={len(reasoning) if reasoning else 0} "
                      f"think_tag_in_content={'<think>' in (content or '') or '</think>' in (content or '')} "
                      f"content={content!r:.60}")
    print("wrote", out_path)


if __name__ == "__main__":
    main()
