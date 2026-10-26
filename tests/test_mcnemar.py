import pytest

import a4_helpers as h


# T-05
def test_t05_fixture_b10_c2():
    r = h.mcnemar_exact(10, 2)
    assert r["p_statsmodels"] == pytest.approx(158 / 4096)
    assert r["p_binomial"] == pytest.approx(158 / 4096)
    assert r["p"] == pytest.approx(0.03857421875)


@pytest.mark.parametrize("b,c", [(0, 0), (5, 5), (0, 7), (3, 9), (1, 0), (40, 25)])
def test_t05_statsmodels_equals_binomial(b, c):
    r = h.mcnemar_exact(b, c)
    assert r["p_statsmodels"] == pytest.approx(r["p_binomial"])
    assert 0.0 <= r["p"] <= 1.0


def test_t05_zero_discordant_is_one():
    assert h.mcnemar_exact(0, 0)["p"] == 1.0


def test_t05_by_id_alignment():
    ids = ["a", "b", "c", "d", "e"]
    ref = dict(zip(ids, ["POSITIVE"] * 5))
    p1 = dict(zip(ids, ["POSITIVE", "POSITIVE", "NEUTRAL", "NEUTRAL", "POSITIVE"]))
    # p2 inserted in reverse order: must still align by id
    p2_vals = {"a": "POSITIVE", "b": "NEUTRAL", "c": "POSITIVE", "d": "NEUTRAL", "e": "POSITIVE"}
    p2 = {k: p2_vals[k] for k in reversed(ids)}
    r = h.mcnemar_by_id(ref, p1, p2)
    # p1 correct: a b e. p2 correct: a c e. b = p1 right and p2 wrong = {b}; c = p1 wrong and p2 right = {c}
    assert (r["b"], r["c"]) == (1, 1)
    with pytest.raises(ValueError):
        h.mcnemar_by_id(ref, p1, {"a": "POSITIVE"})
