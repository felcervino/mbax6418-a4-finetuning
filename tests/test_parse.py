import pytest

import a4_helpers as h


# T-04 strict parse
@pytest.mark.parametrize("raw,exp", [
    ("POSITIVE", "POSITIVE"),
    (" positive\n", "POSITIVE"),
    ("Positive.", "INVALID"),
    ("", "INVALID"),
    ("POSITIVE NEGATIVE", "INVALID"),
    ("Neutral", "NEUTRAL"),
    ("negative", "NEGATIVE"),
    ("NEUTRAL\n\n", "NEUTRAL"),
    ("POS", "INVALID"),
    (None, "INVALID"),
])
def test_t04_parse(raw, exp):
    assert h.parse_label(raw) == exp
