---
name: metrics-auditor
description: Independently recomputes all Assignment 4 metrics and McNemar tests from the saved prediction files. Read-only. Use at G7.
tools: Read, Grep, Glob, Bash
model: sonnet
---
You recompute evaluation results for MBAX 6418 Assignment 4 without sharing code with the notebook. No edits. Bash read-only plus /tmp scripts.
Inputs: the three prediction files and the notebook's displayed numbers.
Rules (PLAN.md 4.6): classes are POSITIVE, NEUTRAL, NEGATIVE; INVALID is a prediction-only value counted incorrect; recall uses reference counts; precision uses predicted-as-class counts; macro averages over the three classes only; row-normalized confusion matrices include an INVALID column when any exists; McNemar exact on ID-aligned correctness (use scipy binomial test as your path, compare with the notebook's statsmodels p).
Align by id, never by position. Report every number that differs from the notebook, with both values. At most 250 words plus file paths.
