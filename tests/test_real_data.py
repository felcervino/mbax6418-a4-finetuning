import os

import pytest

import a4_helpers as h

RAW = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "Gift_Cards.jsonl.gz")
ZIP = os.path.join(os.path.dirname(__file__), "..", "data", "split_data.zip")

pytestmark = pytest.mark.skipif(not (os.path.exists(RAW) and os.path.exists(ZIP)), reason="raw data not present")


def test_run_data_checks_on_real_data():
    surv = list(h.iter_survivors(h.read_gz_lines(RAW)))
    splits = h.build_splits(surv)
    res = h.run_data_checks(surv, splits, h.read_zip_splits(ZIP))
    assert [r["id"] for r in res] == ["C-02", "C-02b", "C-03", "C-04", "C-05", "C-06", "C-07a", "C-08", "C-09", "C-10"]
    assert all(r["pass"] for r in res)


def test_run_data_checks_detects_corruption():
    surv = list(h.iter_survivors(h.read_gz_lines(RAW)))
    splits = h.build_splits(surv)
    zipped = h.read_zip_splits(ZIP)
    zipped["train"] = zipped["train"][::-1]  # order changed
    with pytest.raises(AssertionError):
        h.run_data_checks(surv, splits, zipped)
