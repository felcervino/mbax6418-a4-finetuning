import a4_helpers as h


def test_best_approach_tiebreak():
    m = {"b": {"macro_f1": 0.5, "balanced_accuracy": 0.6}, "a": {"macro_f1": 0.5, "balanced_accuracy": 0.6},
         "c": {"macro_f1": 0.5, "balanced_accuracy": 0.7}, "d": {"macro_f1": 0.4, "balanced_accuracy": 0.9}}
    assert h.best_approach(m) == "c"
    del m["c"]
    assert h.best_approach(m) == "a"  # alphabetical when both ties hold


def test_error_analysis_rule():
    ref = {i: "POSITIVE" for i in range(1, 8)}
    W, R = "NEUTRAL", "POSITIVE"
    zero = {1: W, 2: R, 3: W, 4: R, 5: W, 6: R, 7: R}
    few = {1: W, 2: R, 3: R, 4: R, 5: W, 6: W, 7: R}
    ft = {1: R, 2: W, 3: R, 4: W, 5: W, 6: R, 7: R}
    ea = h.error_analysis(ref, zero, few, ft, n=1)
    assert ea["fixed_by_ft"] == {"total": 1, "ids": [1]}          # only id 1: ft right, both hosted wrong
    assert ea["broken_by_ft"] == {"total": 2, "ids": [2]}         # ids 2 and 4: ft wrong, both hosted right
    assert ea["wrong_in_all"] == {"total": 1, "ids": [5]}


def test_pairwise_mcnemar_pairs():
    ref = {1: "POSITIVE", 2: "POSITIVE"}
    r = h.pairwise_mcnemar(ref, {"z": {1: "POSITIVE", 2: "NEUTRAL"}, "f": {1: "POSITIVE", 2: "POSITIVE"},
                                 "t": {1: "NEUTRAL", 2: "POSITIVE"}})
    assert set(r) == {"f vs t", "f vs z", "t vs z"}
