# G1 data-auditor result (transcribed by Claude from the subagent's report, 2026-10-26)

The auditor rebuilt the splits from the raw gz with stdlib only, without reading src/a4_helpers.py or tools/check_data.py. Its script (/tmp/aud/a.py) was not saved to the repo.

PASS: counts and class balance (900/300/300), ids and (filtered_index, original_row) pairs equal to zip, train order equal to zip (val and test order also), title/text/rating/label equal by id, ranges, unique ids, zero overlap, ratings consistent with labels.
Raw file: 152410 lines, 1170 skipped as too short, 151240 survivors, 0 blank lines, 0 missing or non-string text, 0 non-string titles, ratings only 1.0 to 5.0, original_row gaps only at skipped lines.
Surprises: none. Zip records carry asin, user_id, timestamp, helpful_vote, verified_purchase (not compared).
