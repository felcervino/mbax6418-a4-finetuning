import json

import pytest

import a4_helpers as h


# T-08 prediction writer/reader round trip
def test_t08_roundtrip(tmp_path):
    recs = []
    raws = ["POSITIVE", " neutral\n", 'say "hi"\r\nnew\tline', "café — \U0001F600", "  ", ""]
    for i, raw in enumerate(raws):
        recs.append({"original_row": i + 1, "filtered_index": 30000 + i, "title": 'a "t"\nx',
                     "text": "line1\nline2  café", "reference_label": "POSITIVE",
                     "prediction": h.parse_label(raw), "raw_response": raw})
    p = tmp_path / "p.jsonl"
    h.write_predictions(str(p), recs)
    back = h.read_predictions(str(p))
    assert back == recs
    raw_bytes = p.read_bytes().decode("utf-8")
    first = json.loads(raw_bytes.split("\n")[0])
    assert list(first.keys()) == h.PREDICTION_FIELDS
    assert len(raw_bytes.split("\n")) == len(recs) + 1  # one physical line per record


def test_t08_rejects_wrong_fields(tmp_path):
    with pytest.raises(ValueError):
        h.write_predictions(str(tmp_path / "x.jsonl"), [{"original_row": 1}])
