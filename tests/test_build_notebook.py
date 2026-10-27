import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import build_notebook as bn  # noqa: E402


def test_notebook_builds_and_scans_clean(tmp_path):
    nb, n = bn.build(str(tmp_path / "nb.ipynb"))
    assert n >= 10
    sources = [c.source for c in nb.cells if c.cell_type == "code"]
    assert any("COMPLETE SAVED-ADAPTER INFERENCE EXAMPLE" in c.source for c in nb.cells if c.cell_type == "markdown")
    assert any("S4" in s.split("\n")[0] or "run_hosted" in s for s in sources)


def test_scan_catches_reserved_set_read():
    import a4_helpers as h
    with pytest.raises(AssertionError):
        h.scan_forbidden_tokens(["x = splits['val']"], [r"\bval\b"])
    with pytest.raises(AssertionError):
        h.scan_forbidden_tokens(["labels = SEALED_TEST_LABELS"], [r"SEALED"])


def test_sections_order():
    with open(bn.CELLS, encoding="utf-8") as f:
        cells = bn.parse_cells(f.read())
    nums = [bn.section_number(c["tag"]) for c in cells if c["type"] == "code"]
    nums = [n for n in nums if n is not None]
    assert nums == sorted(nums)
    assert 8 in nums and 6 in nums and 5 in nums
