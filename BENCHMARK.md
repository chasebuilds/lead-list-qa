# Benchmark

Written by `benchmark/run_benchmark.py` on 2026-11-21 from a real run.
No number on this page was typed by hand.

Command: `python -m benchmark.run_benchmark --seed 20261121 --people 5000`
Python 3.11.15 on Windows.
Checking all 5,000 rows took 0.23 s.

## Method

1. Invent 5,000 fake contacts: made-up first and last names, made-up companies on
   `.example` domains, US phone numbers in the 555-0100 to 555-0199 range written five ways, and
   titles drawn from five seniority buckets with the right bucket stored. No real person is used.
2. About 30% of rows get exactly one planted fault: broken email syntax, a role address
   (`info@`, `sales@`), a disposable domain, a free-mail domain, a bad phone, a blank required
   field, a repeat of an earlier person by email (different case and spacing), or a repeat by
   name and company with a different email.
3. Run the checks. A fault counts as caught only when the row carries that exact reason (or, for
   repeats, lands in Removed duplicates). A clean row counts as a false flag when it gets any
   reason or is marked as a duplicate.

## Result

| Measure | Result |
|---|---:|
| Rows | 5,000 |
| Caught: `email_syntax` | **100.0%** (196 of 196) |
| Caught: `role` | **100.0%** (185 of 185) |
| Caught: `disposable` | **100.0%** (180 of 180) |
| Caught: `freemail` | **100.0%** (187 of 187) |
| Caught: `phone` | **100.0%** (207 of 207) |
| Caught: `missing` | **100.0%** (178 of 178) |
| Caught: `dup_email` | **100.0%** (207 of 207) |
| Caught: `dup_name` | **100.0%** (191 of 191) |
| Caught: all planted faults | **100.0%** (1,531 of 1,531) |
| Clean rows flagged by mistake | **0.0%** (0 of 3,469) |
| Title bucket right on clean rows | **100.0%** (3,469 of 3,469) |

## What this does not show

The faults are planted by the same person who wrote the checks, so the test covers the cases
that were thought of. Real lists have faults nobody planted here: misspelled names, people who
left the company, inboxes that no longer exist. See [LIMITATIONS.md](LIMITATIONS.md).
