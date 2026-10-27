import pytest

import a4_helpers as h


class FakeTok:
    bos_token = "<bos>"

    def apply_chat_template(self, messages, tokenize=False):
        return "<bos>" + "".join(m["content"] for m in messages)


def test_render_strips_leading_bos_only_once():
    t = h.render_chat_text(FakeTok(), [{"role": "user", "content": "hi"}])
    assert t == "hi"
    assert h.render_chat_text(FakeTok(), [{"role": "user", "content": "hi"}], strip_bos=False) == "<bos>hi"


def test_prefix_check():
    h.check_prompt_is_training_prefix([2, 5, 6], [2, 5, 6, 9, 1])
    with pytest.raises(AssertionError):
        h.check_prompt_is_training_prefix([2, 2, 5], [2, 5, 6, 9, 1])  # doubled or missing BOS
    with pytest.raises(AssertionError):
        h.check_prompt_is_training_prefix([2, 5, 6], [2, 5, 6])  # no target after the prompt


def test_canonical_fingerprint_is_deterministic_and_sensitive():
    fs = [("a", "b", "POSITIVE")]
    a = h.config_hash(h.canonical_prompt_fingerprint(fs))
    assert a == h.config_hash(h.canonical_prompt_fingerprint(fs))
    assert a != h.config_hash(h.canonical_prompt_fingerprint([("a", "b", "NEGATIVE")]))
    assert h.canonical_prompt_fingerprint(fs)["parse_table"] == ["POSITIVE", "NEUTRAL", "INVALID", "INVALID", "INVALID", "INVALID"]
