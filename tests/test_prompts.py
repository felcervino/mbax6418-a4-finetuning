import inspect
import json
import zipfile

import pytest

import a4_helpers as h


# T-06
def test_t06_builder_signature_is_title_text_only():
    assert list(inspect.signature(h.build_messages_zero_shot).parameters) == ["title", "text"]
    assert list(inspect.signature(h.build_messages_few_shot).parameters) == ["title", "text", "examples"]
    assert list(inspect.signature(h.build_messages_fine_tuned).parameters) == ["title", "text", "target"]


def test_t06_exact_format():
    m = h.build_messages_zero_shot("Five Stars", "Loved it.\nTwice.")
    assert m == [
        {"role": "system", "content": "You are an expert product review analyst. Determine the sentiment each Amazon review expresses."},
        {"role": "user", "content": "Classify the sentiment of the review below as exactly one of: POSITIVE, NEUTRAL, NEGATIVE. Reply with exactly one word, no explanation.\n\nReview title: Five Stars\nReview text: Loved it.\nTwice."},
    ]


def test_t06_deterministic_and_unmodified():
    a = h.build_messages_zero_shot("  TiTle ", " Text\t ")
    b = h.build_messages_zero_shot("  TiTle ", " Text\t ")
    assert a == b and "Review title:   TiTle \n" in a[1]["content"]


def test_t06_few_shot_ordering_and_instruction_identity():
    ex = [("t1", "x1", "POSITIVE"), ("t2", "x2", "NEUTRAL"), ("t3", "x3", "NEGATIVE")]
    fs = h.build_messages_few_shot("T", "X", ex)
    zs = h.build_messages_zero_shot("T", "X")
    assert [m["role"] for m in fs] == ["system"] + ["user", "assistant"] * 3 + ["user"]
    assert fs[0] == zs[0]
    assert [fs[2 * i + 2]["content"] for i in range(3)] == ["POSITIVE", "NEUTRAL", "NEGATIVE"]
    assert fs[1] == h.build_messages_zero_shot("t1", "x1")[1]
    assert fs[-1] == zs[1]
    # C-14b: instruction text identical across approaches
    assert h.instruction_hash(zs) == h.instruction_hash(fs) == h.instruction_hash(h.build_messages_fine_tuned("T", "X"))


def test_t06_few_shot_rejects_bad_label():
    with pytest.raises(ValueError):
        h.build_messages_few_shot("T", "X", [("a", "b", "INVALID")])


# C-14 sentinel: altering rating/label cannot change output
def test_c14_sentinel():
    base = {"title": "t", "text": "x", "rating": 5.0, "reference_label": "POSITIVE"}
    alt = dict(base, rating=1.0, reference_label="NEGATIVE")
    assert h.build_prompt_for_record(base) == h.build_prompt_for_record(alt)
    assert "POSITIVE" not in json.dumps(h.build_prompt_for_record(base)[1:]).replace("POSITIVE, NEUTRAL, NEGATIVE", "")


def test_fine_tuned_messages_with_target():
    m = h.build_messages_fine_tuned("t", "x", target="NEUTRAL")
    assert m[-1] == {"role": "assistant", "content": "NEUTRAL"}
    assert h.build_messages_fine_tuned("t", "x") == h.build_messages_zero_shot("t", "x")
    with pytest.raises(ValueError):
        h.build_messages_fine_tuned("t", "x", target="maybe")


# T-07
def _mk(tmp_path, names):
    d = tmp_path / "a"
    d.mkdir(exist_ok=True)
    out = []
    for n in names:
        (d / n).write_bytes(b"x" + n.encode())
        out.append(str(d / n))
    return out


def test_t07_zip_builder_two_files(tmp_path):
    paths = _mk(tmp_path, ["adapter_model.safetensors", "adapter_config.json"])
    z = tmp_path / "adapter.zip"
    h.build_adapter_zip(paths, str(z))
    assert sorted(zipfile.ZipFile(z).namelist()) == ["adapter_config.json", "adapter_model.safetensors"]
    h.verify_adapter_zip(str(z))


def test_t07_zip_builder_refuses_extra(tmp_path):
    paths = _mk(tmp_path, ["adapter_model.safetensors", "adapter_config.json", "README.md"])
    with pytest.raises(ValueError):
        h.build_adapter_zip(paths, str(tmp_path / "bad.zip"))
    assert not (tmp_path / "bad.zip").exists()


def test_t07_verifier_fails_on_three_files_and_folder(tmp_path):
    z = tmp_path / "three.zip"
    with zipfile.ZipFile(z, "w") as zf:
        for n in ["adapter_model.safetensors", "adapter_config.json", "tokenizer.json"]:
            zf.writestr(n, "x")
    with pytest.raises(ValueError):
        h.verify_adapter_zip(str(z))
    z2 = tmp_path / "folder.zip"
    with zipfile.ZipFile(z2, "w") as zf:
        for n in ["adapter/adapter_model.safetensors", "adapter/adapter_config.json"]:
            zf.writestr(n, "x")
    with pytest.raises(ValueError):
        h.verify_adapter_zip(str(z2))
