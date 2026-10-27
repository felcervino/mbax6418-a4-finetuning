"""tools/freeze.py must compute the same hash as notebook cell S3 and react to any frozen change."""
import os
import sys

import pytest

import a4_helpers as h

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import freeze  # noqa: E402

needs_zip = pytest.mark.skipif(not os.path.exists(freeze.ZIP), reason="data/split_data.zip not present")


def _cells():
    with open(freeze.CELLS, encoding="utf-8") as f:
        return f.read()


def test_read_config_from_cells():
    cfg, keys, extra, approved = freeze.read_config(_cells())
    assert keys == ["prompt", "hosted", "fewshot_ids", "small_model", "train", "flip_rate"]
    assert extra == ["instruction_hash", "canonical_prompts", "flip_ids"]
    assert cfg["prompt"] == {"system": h.SYSTEM_PROMPT, "instruction": h.USER_INSTRUCTION}
    assert approved is None or isinstance(approved, str)


@needs_zip
def test_hash_matches_notebook_formula_and_is_sensitive():
    cfg, keys, extra, _ = freeze.read_config(_cells())
    train = freeze.read_train()
    obj, full = freeze.compute(cfg, keys, extra, train)
    assert set(obj) == set(keys + extra) and full == h.config_hash(obj)
    assert len(obj["flip_ids"]) == 30
    _, again = freeze.compute(cfg, keys, extra, list(reversed(train)))
    assert again == full
    changed = dict(cfg, hosted=dict(cfg["hosted"], max_tokens=cfg["hosted"]["max_tokens"] + 1))
    assert freeze.compute(changed, keys, extra, train)[1] != full
    changed = dict(cfg, flip_rate=dict(cfg["flip_rate"], seed=cfg["flip_rate"]["seed"] + 1))
    assert freeze.compute(changed, keys, extra, train)[1] != full


def test_unknown_extra_key_is_refused():
    cfg, keys, _, _ = freeze.read_config(_cells())
    with pytest.raises(AssertionError):
        freeze.compute(cfg, keys, ["something_new"], [])
