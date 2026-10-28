"""tools/scan_secrets.py finds credential-shaped strings and never prints their values."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import scan_secrets as ss  # noqa: E402

FAKE_BEARER = "Authorization: Bearer " + "a1b2c3d4e5f6" * 4
FAKE_HF = "hf_" + "AbCdEfGhIj" * 4
FAKE_ASSIGN = 'API_KEY = "' + "Zx9" * 8 + '"'


def test_detects_credential_shapes(tmp_path):
    for name, content in (("a.txt", FAKE_BEARER), ("b.py", FAKE_HF), ("c.py", FAKE_ASSIGN)):
        (tmp_path / name).write_text(content, encoding="utf-8")
    hits = ss.scan_paths([str(tmp_path)])
    assert {x["file"] for x in hits} == {"a.txt", "b.py", "c.py"}


def test_clean_files_and_review_text_pass(tmp_path):
    (tmp_path / "ok.txt").write_text("The card needed authorization at the till. api_key is read from Colab Secrets.", encoding="utf-8")
    (tmp_path / "code.py").write_text('API_KEY = userdata.get("CLASS_API_KEY")\nkey = os.environ.get("CLASS_API_KEY")', encoding="utf-8")
    assert ss.scan_paths([str(tmp_path)]) == []


def test_hits_never_contain_the_secret_value(tmp_path):
    (tmp_path / "a.txt").write_text(FAKE_BEARER, encoding="utf-8")
    hits = ss.scan_paths([str(tmp_path)])
    assert hits and all("a1b2c3d4e5f6" not in str(x) for x in hits)


def test_exact_value_scan_skips_short_values_and_finds_long_ones(tmp_path, monkeypatch):
    (tmp_path / "a.txt").write_text("contains " + "Q7" * 12 + " inside", encoding="utf-8")
    monkeypatch.setenv("CLASS_API_KEY", "Q7" * 12)
    assert [x["file"] for x in ss.scan_paths([str(tmp_path)])] == ["a.txt"]
    monkeypatch.setenv("CLASS_API_KEY", "1234")
    (tmp_path / "a.txt").write_text("MBAX 6418", encoding="utf-8")
    assert ss.scan_paths([str(tmp_path)]) == []
    assert ss.exact_value_status().startswith("skipped")


def test_notebook_outputs_are_scanned(tmp_path):
    nb = {"cells": [{"cell_type": "code", "source": ["x"], "execution_count": 1,
                     "outputs": [{"output_type": "stream", "text": [FAKE_HF]}]}], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}
    (tmp_path / "n.ipynb").write_text(json.dumps(nb), encoding="utf-8")
    assert [x["file"] for x in ss.scan_paths([str(tmp_path)])] == ["n.ipynb"]
