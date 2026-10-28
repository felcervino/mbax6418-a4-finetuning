"""C-23 secret scan. Finds credential-shaped strings; hits show file, line and kind, never the matched text.

Usage: python tools/scan_secrets.py [path ...]   (default: the whole repo except .git and data/raw)
If the environment variable CLASS_API_KEY holds a value of at least 12 characters, files are also searched for that
exact value (still never printed). A shorter value would match ordinary text, so the exact search is skipped then.
Exit code 1 when anything is found.
"""
import os
import re
import sys

PATTERNS = {
    "bearer_token": re.compile(r"Bearer\s+[A-Za-z0-9._\-]{20,}"),
    "hf_token": re.compile(r"\bhf_[A-Za-z0-9]{20,}"),
    "sk_key": re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}"),
    "assigned_secret": re.compile(r"(?i)\b(api[_-]?key|secret|token|passw(?:or)?d)\b\s*[:=]\s*[\"'][A-Za-z0-9_\-+/=]{16,}[\"']"),
}
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".ipynb_checkpoints", "raw", "node_modules"}
SKIP_EXT = {".zip", ".gz", ".png", ".jpg", ".jpeg", ".safetensors", ".pdf", ".pptx", ".wav", ".pyc"}
MAX_BYTES = 60 * 1024 * 1024
MIN_EXACT_LEN = 12


def exact_value_status():
    v = os.environ.get("CLASS_API_KEY")
    if not v:
        return "skipped: CLASS_API_KEY not set in this environment"
    if len(v) < MIN_EXACT_LEN:
        return "skipped: value shorter than 12 characters, exact search would match ordinary text"
    return "active"


def _files(paths):
    for top in paths:
        if os.path.isfile(top):
            yield os.path.dirname(top) or ".", top
            continue
        for dp, dns, fns in os.walk(top):
            dns[:] = [d for d in dns if d not in SKIP_DIRS]
            for fn in fns:
                if os.path.splitext(fn)[1].lower() in SKIP_EXT:
                    continue
                yield top, os.path.join(dp, fn)


def scan_paths(paths):
    exact = os.environ.get("CLASS_API_KEY") if exact_value_status() == "active" else None
    hits = []
    for base, path in _files(paths):
        try:
            if os.path.getsize(path) > MAX_BYTES:
                continue
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.read().split("\n")
        except OSError:
            continue
        rel = os.path.relpath(path, base).replace("\\", "/")
        for n, line in enumerate(lines, 1):
            for kind, pat in PATTERNS.items():
                if pat.search(line):
                    hits.append({"file": rel, "line": n, "kind": kind})
            if exact and exact in line:
                hits.append({"file": rel, "line": n, "kind": "exact_class_key"})
    return hits


def main():
    root = os.path.join(os.path.dirname(__file__), "..")
    paths = sys.argv[1:] or [root]
    hits = scan_paths(paths)
    for x in hits:
        print(f"HIT {x['file']}:{x['line']} {x['kind']}")
    print(f"exact class-key search: {exact_value_status()}")
    print(f"C-23: {'FAIL' if hits else 'PASS'} | {len(hits)} hit(s) in {', '.join(paths)}")
    sys.exit(1 if hits else 0)


if __name__ == "__main__":
    main()
