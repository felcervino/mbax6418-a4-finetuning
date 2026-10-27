import json
import os

import pytest

import a4_helpers as h

CFG = {"base_url": "http://x/v1", "model": "m", "temperature": 0, "max_tokens": 8,
       "extra_body": {"chat_template_kwargs": {"enable_thinking": False}},
       "timeout_s": 5, "max_retries": 2, "retry_backoff_s": 0}
MSGS = h.build_messages_zero_shot("t", "some review text")


def _resp(content="POSITIVE", finish="stop", reasoning=None, rtok=0, ctok=3):
    return json.dumps({"id": "c1", "usage": {"completion_tokens": ctok, "completion_tokens_details": {"reasoning_tokens": rtok}},
                       "choices": [{"index": 0, "finish_reason": finish,
                                    "message": {"role": "assistant", "content": content, "reasoning": reasoning}}]})


class FakePost:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def __call__(self, url, body, api_key, timeout):
        self.calls.append((url, body, api_key))
        o = self.outcomes.pop(0)
        if isinstance(o, Exception):
            raise o
        return o


def test_config_hash_stable_and_sensitive():
    assert h.config_hash({"a": 1, "b": [1, 2]}) == h.config_hash({"b": [1, 2], "a": 1})
    assert h.config_hash({"a": 1}) != h.config_hash({"a": 2})


def test_call_hosted_success_and_cache(tmp_path):
    fp = FakePost([(200, _resp())])
    r1 = h.call_hosted(MSGS, CFG, "KEY", str(tmp_path), "frozen1", post=fp)
    assert r1["content"] == "POSITIVE" and r1["prediction"] == "POSITIVE" and r1["violations"] == []
    assert r1["from_cache"] is False and len(fp.calls) == 1
    body = fp.calls[0][1]
    assert body["temperature"] == 0 and body["max_tokens"] == 8
    assert body["chat_template_kwargs"] == {"enable_thinking": False}
    assert body["messages"] == MSGS
    # cache hit: no second POST, same raw response
    fp2 = FakePost([])
    r2 = h.call_hosted(MSGS, CFG, "KEY", str(tmp_path), "frozen1", post=fp2)
    assert r2["from_cache"] is True and r2["raw"] == r1["raw"] and fp2.calls == []
    # different frozen hash is a different cache key
    fp3 = FakePost([(200, _resp("NEUTRAL"))])
    r3 = h.call_hosted(MSGS, CFG, "KEY", str(tmp_path), "frozen2", post=fp3)
    assert r3["prediction"] == "NEUTRAL" and len(fp3.calls) == 1


def test_key_never_stored(tmp_path):
    fp = FakePost([(200, _resp())])
    h.call_hosted(MSGS, CFG, "SECRET-KEY-123", str(tmp_path), "f", post=fp)
    for name in os.listdir(tmp_path):
        assert "SECRET-KEY-123" not in open(os.path.join(tmp_path, name), encoding="utf-8").read()


def test_retry_only_on_transport_and_5xx(tmp_path):
    fp = FakePost([h.TransportError("timeout"), (503, "busy"), (200, _resp())])
    r = h.call_hosted(MSGS, CFG, "K", str(tmp_path), "f", post=fp, sleep=lambda s: None)
    assert r["prediction"] == "POSITIVE" and len(fp.calls) == 3 and r["attempts"] == 3
    fp = FakePost([h.TransportError("t")] * 3)
    with pytest.raises(h.TransportError):
        h.call_hosted(MSGS, CFG, "K", str(tmp_path / "b"), "f", post=fp, sleep=lambda s: None)
    assert len(fp.calls) == 3  # 1 try + 2 retries


def test_4xx_not_retried(tmp_path):
    fp = FakePost([(401, '{"error":"Unauthorized"}')])
    with pytest.raises(RuntimeError):
        h.call_hosted(MSGS, CFG, "K", str(tmp_path), "f", post=fp)
    assert len(fp.calls) == 1


def test_bad_content_not_retried_and_invalid(tmp_path):
    fp = FakePost([(200, _resp("Positive."))])
    r = h.call_hosted(MSGS, CFG, "K", str(tmp_path), "f", post=fp)
    assert r["prediction"] == "INVALID" and r["content"] == "Positive." and len(fp.calls) == 1


def test_violations_recorded_not_hidden(tmp_path):
    fp = FakePost([(200, _resp(None, finish="length", reasoning="hmm", rtok=8, ctok=8))])
    r = h.call_hosted(MSGS, CFG, "K", str(tmp_path), "f", post=fp)
    assert r["prediction"] == "INVALID"
    assert set(r["violations"]) == {"finish_reason:length", "reasoning_present", "reasoning_tokens:8"}


def test_cache_write_retries_when_replace_fails_transiently(tmp_path, monkeypatch):
    """Drive-backed folders can report FileNotFoundError on the tmp-to-final rename (final run, cell S4). The answer is
    already in memory, so the write is retried and the hosted API is called exactly once."""
    real = os.replace
    fails = {"n": 2}

    def flaky(src, dst):
        if fails["n"] > 0:
            fails["n"] -= 1
            raise FileNotFoundError(2, "No such file or directory", src)
        return real(src, dst)

    monkeypatch.setattr(os, "replace", flaky)
    fp = FakePost([(200, _resp())])
    r = h.call_hosted(MSGS, CFG, "KEY", str(tmp_path), "frozen1", post=fp, sleep=lambda s: None)
    assert r["prediction"] == "POSITIVE" and r["from_cache"] is False
    assert len(fp.calls) == 1 and fails["n"] == 0
    r2 = h.call_hosted(MSGS, CFG, "KEY", str(tmp_path), "frozen1", post=FakePost([]), sleep=lambda s: None)
    assert r2["from_cache"] is True and r2["content"] == "POSITIVE"
    assert not [f for f in os.listdir(tmp_path) if f.endswith(".tmp")]


def test_cache_write_gives_up_loudly_and_never_rerolls(tmp_path, monkeypatch):
    def always(src, dst):
        raise FileNotFoundError(2, "No such file or directory", src)

    monkeypatch.setattr(os, "replace", always)
    fp = FakePost([(200, _resp())])
    with pytest.raises(FileNotFoundError):
        h.call_hosted(MSGS, CFG, "KEY", str(tmp_path), "frozen1", post=fp, sleep=lambda s: None)
    assert len(fp.calls) == 1
