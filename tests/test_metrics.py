import math

import pytest

import a4_helpers as h

REFS = ["POSITIVE"] * 4 + ["NEUTRAL"] * 3 + ["NEGATIVE"] * 3
PREDS = (["POSITIVE", "POSITIVE", "NEUTRAL", "INVALID"]
         + ["NEUTRAL", "POSITIVE", "NEGATIVE"]
         + ["NEGATIVE", "NEGATIVE", "NEUTRAL"])


# T-03 hand-computed fixture.
# recall: POS 2/4, NEU 1/3, NEG 2/3. precision: POS 2/3, NEU 1/3, NEG 2/3.
# F1: POS 4/7, NEU 1/3, NEG 2/3. macro-F1 = 11/21. balanced accuracy = 1/2.
def test_t03_metrics():
    m = h.compute_metrics(REFS, PREDS)
    assert m["correct"] == 5 and m["incorrect"] == 5 and m["invalid"] == 1
    pc = m["per_class"]
    assert pc["POSITIVE"]["recall"] == pytest.approx(0.5)
    assert pc["NEUTRAL"]["recall"] == pytest.approx(1 / 3)
    assert pc["NEGATIVE"]["recall"] == pytest.approx(2 / 3)
    assert pc["POSITIVE"]["precision"] == pytest.approx(2 / 3)
    assert pc["NEUTRAL"]["precision"] == pytest.approx(1 / 3)
    assert pc["NEGATIVE"]["precision"] == pytest.approx(2 / 3)
    assert pc["POSITIVE"]["f1"] == pytest.approx(4 / 7)
    assert pc["NEUTRAL"]["f1"] == pytest.approx(1 / 3)
    assert pc["NEGATIVE"]["f1"] == pytest.approx(2 / 3)
    assert m["macro_f1"] == pytest.approx(11 / 21)
    assert m["balanced_accuracy"] == pytest.approx(0.5)
    assert pc["POSITIVE"]["correct"] == 2 and pc["POSITIVE"]["incorrect"] == 2
    assert pc["POSITIVE"]["n"] == 4


def test_t03_confusion_and_normalization():
    cm = h.confusion_matrix(REFS, PREDS)
    assert h.CM_COLUMNS == ["POSITIVE", "NEUTRAL", "NEGATIVE", "INVALID"]
    assert cm == [[2, 1, 0, 1], [1, 1, 1, 0], [0, 1, 2, 0]]
    norm = h.normalize_rows(cm)
    assert norm[0] == pytest.approx([0.5, 0.25, 0.0, 0.25])
    for row in norm:
        assert sum(row) == pytest.approx(1.0)


def test_t03_sklearn_crosscheck_where_valid():
    from sklearn.metrics import balanced_accuracy_score, f1_score
    refs = ["POSITIVE", "NEUTRAL", "NEGATIVE", "NEGATIVE", "POSITIVE", "NEUTRAL"]
    preds = ["POSITIVE", "NEGATIVE", "NEGATIVE", "NEUTRAL", "NEUTRAL", "NEUTRAL"]
    m = h.compute_metrics(refs, preds)
    assert m["balanced_accuracy"] == pytest.approx(balanced_accuracy_score(refs, preds))
    assert m["macro_f1"] == pytest.approx(f1_score(refs, preds, average="macro", labels=h.LABELS))


def test_t03_zero_division_is_zero():
    m = h.compute_metrics(["POSITIVE", "NEUTRAL", "NEGATIVE"], ["INVALID"] * 3)
    assert m["macro_f1"] == 0.0 and m["balanced_accuracy"] == 0.0
    assert all(math.isfinite(v["precision"]) for v in m["per_class"].values())


def test_t03_bad_inputs_rejected():
    with pytest.raises(ValueError):
        h.compute_metrics(["INVALID"], ["POSITIVE"])
    with pytest.raises(ValueError):
        h.compute_metrics(["POSITIVE"], ["MAYBE"])
    with pytest.raises(ValueError):
        h.compute_metrics(["POSITIVE"], [])
