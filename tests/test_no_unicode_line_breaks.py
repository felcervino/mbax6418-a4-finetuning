"""Colab's editor treats U+2028, U+2029 and U+0085 as line breaks, so a literal one inside a string splits the line and
breaks the cell (SyntaxError seen in the final run). Python itself accepts them, so only this test catches it.
This file builds the characters with chr() so it never contains one itself."""
import json
import os

import pytest

import a4_helpers as h

ROOT = os.path.join(os.path.dirname(__file__), "..")
LS, PS, NEL = chr(0x2028), chr(0x2029), chr(0x85)
BAD = {LS: "U+2028", PS: "U+2029", NEL: "U+0085"}
SOURCES = ["src/a4_helpers.py", "notebook_src/a4_cells.py", "build/a4_finetune.ipynb", "tests/test_no_unicode_line_breaks.py"]


@pytest.mark.parametrize("rel", SOURCES)
def test_no_literal_unicode_line_breaks(rel):
    path = os.path.join(ROOT, rel)
    if not os.path.exists(path):
        pytest.skip(f"{rel} not present")
    text = open(path, encoding="utf-8").read()
    found = {name: text.count(ch) for ch, name in BAD.items() if ch in text}
    assert not found, f"{rel} contains literal line-break characters {found}; write them as escape sequences"


def test_write_predictions_still_escapes_separators(tmp_path):
    rec = {k: "" for k in h.PREDICTION_FIELDS}
    rec["raw_response"] = "a" + LS + "b" + PS + "c"
    p = str(tmp_path / "p.jsonl")
    h.write_predictions(p, [rec])
    raw = open(p, encoding="utf-8", newline="").read()
    assert LS not in raw and PS not in raw
    assert chr(92) + "u2028" in raw and chr(92) + "u2029" in raw
    assert json.loads(raw)["raw_response"] == "a" + LS + "b" + PS + "c"
