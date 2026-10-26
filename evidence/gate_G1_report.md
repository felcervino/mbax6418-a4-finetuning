GATE G1 REPORT
Phase: 1 Data layer      Date: 2026-10-26      Commit candidate: none yet (Felipe's OK on status and message needed)

Checks:
- C-01 raw readable: PASS, 12292543 bytes, sha256 e03a258e..., 152410 lines (evidence/gate_G1_data_checks.log)
- C-02 (filtered_index, original_row) pairs equal zip, all 3 sets: PASS; fields equal by id: PASS
- C-03 labels from rating: PASS (0 mismatches)
- C-04 index ranges: PASS
- C-05 train records AND order from Random(43): PASS
- C-06 test = first 100/class: PASS. C-07 val = first 100/class: PASS (no-val-read scan is a Phase 3 notebook check)
- C-08 sizes and classes: PASS (900 at 300 each; 300 at 100 each)
- C-09 unique ids: PASS. C-10 no overlap: PASS
- Tests T-01..T-08 plus C-14 sentinel: 56 passed (evidence/gate_G1_pytest.log)

Requirements advanced: C-01..C-10 PASS locally; notebook-side versions still to come in Phase 3.

Anomalies and surprises:
1. 1170 raw texts under 3 chars (skipped); all gaps in original_row are explained by them.
2. Raw class skew is strong: 5 stars is 84% of ratings. Only the splits are balanced.
3. Zip records carry extra fields (asin, user_id, timestamp, helpful_vote, verified_purchase). Not used.
4. Venv path is redirected by the app into its package cache (outside OneDrive).
5. Prompt builders are provisional (D-01/D-02 open). The zip's val file was read only for this verification.
6. Bash heredoc failed once on a long command; files were written with the Write tool instead.

Decisions needing Felipe: none. Please spot-check IDs, class counts, overlap (evidence/gate_G1_spotcheck.md).
Unverified claims still open: none for data. Raw file is from the PDF URL; Last-Modified 2025-01-16.
Audit: data-auditor, verdict all PASS, independent stdlib rebuild, nothing surprising (transcribed to evidence/gate_G1_audit.md; script was in the auditor's /tmp, not saved).
Next: after GO G1, commit, then Phase 2 decisions (Unsloth docs fetch, D-01..D-09 proposals).
STOP. Awaiting "GO G1".
