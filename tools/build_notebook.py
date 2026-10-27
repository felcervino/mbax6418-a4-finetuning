"""Build build/a4_finetune.ipynb from notebook_src/a4_cells.py, inlining src/a4_helpers.py as the first code cell.

Also runs the static scans (C-07 and sealed-label rules) and compiles every cell.
Usage: python tools/build_notebook.py [out_path]
"""
import ast
import os
import re
import sys

import nbformat

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
import a4_helpers as h  # noqa: E402

CELLS = os.path.join(ROOT, "notebook_src", "a4_cells.py")
HELPERS = os.path.join(ROOT, "src", "a4_helpers.py")
HEADER = re.compile(r"^# %%(?: \[(?P<tag>[^\]]+)\])?(?P<title> .*)?$")


def parse_cells(text):
    cells, cur = [], None
    for line in text.split("\n"):
        m = HEADER.match(line)
        if m:
            if cur:
                cells.append(cur)
            tag = m.group("tag") or ""
            cur = {"tag": tag, "title": (m.group("title") or "").strip(), "lines": []}
        elif cur is not None:
            cur["lines"].append(line)
    if cur:
        cells.append(cur)
    out = []
    for c in cells:
        body = "\n".join(c["lines"]).strip("\n")
        if c["tag"] == "markdown":
            body = "\n".join(l[2:] if l.startswith("# ") else l.lstrip("#") for l in body.split("\n"))
            out.append({"type": "markdown", "tag": "markdown", "source": body})
        else:
            out.append({"type": "code", "tag": c["tag"], "title": c["title"], "source": body})
    return out


def section_number(tag):
    m = re.match(r"S(\d+)", tag or "")
    return int(m.group(1)) if m else None


def build(out_path):
    with open(CELLS, encoding="utf-8") as f:
        cells = parse_cells(f.read())
    with open(HELPERS, encoding="utf-8") as f:
        helper_src = f.read()
    ast.parse(helper_src)
    nb = nbformat.v4.new_notebook()
    nb.cells.append(nbformat.v4.new_markdown_cell(cells[0]["source"]))
    nb.cells.append(nbformat.v4.new_code_cell("# [S0] HELPERS (inlined from src/a4_helpers.py, unit-tested locally)\n" + helper_src))
    for c in cells[1:]:
        if c["type"] == "markdown":
            nb.cells.append(nbformat.v4.new_markdown_cell(c["source"]))
        else:
            ast.parse(c["source"])  # raises SyntaxError on a broken cell
            nb.cells.append(nbformat.v4.new_code_cell(c["source"]))
    # Static scans. Sections S2..S7, S9, S10 must not touch the reserved set or the sealed test labels, and must not
    # rebuild splits. S8 is the only section allowed to read SEALED_TEST_LABELS.
    untagged = [c["title"] or c["source"][:40] for c in cells[1:] if c["type"] == "code" and section_number(c["tag"]) is None]
    assert not untagged, f"every code cell needs a section tag, missing on: {untagged}"
    scanned = [c["source"] for c in cells if c["type"] == "code" and (section_number(c["tag"]) or 0) >= 2
               and section_number(c["tag"]) != 8]
    h.scan_forbidden_tokens(scanned, [r"\bval\b", r"SEALED", r"read_zip_splits", r"build_splits", r"split_data",
                                      r"(?<![A-Z_])RAW_PATH", r"(?<![A-Z_])ZIP_PATH", r"test\.jsonl", r"val\.jsonl",
                                      r"globals\(\)", r"\bexec\(", r"\beval\("])
    s8 = [c["source"] for c in cells if c["type"] == "code" and section_number(c["tag"]) == 8]
    h.scan_forbidden_tokens(s8, [r"\bval\b", r"read_zip_splits", r"build_splits"])
    for cell in nb.cells:
        assert "!pip" not in cell.source and "%%" not in cell.source, "shell magics are not allowed"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    nbformat.write(nb, out_path)
    nbformat.validate(nb)
    return nb, len(scanned)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "build", "a4_finetune.ipynb")
    nb, n = build(out)
    print(f"built {out}: {len(nb.cells)} cells; static scan clean over {n} code cells (S2-S7, S9, S10) plus S8 rules")
