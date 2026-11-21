"""Score the checks on lists with planted faults; write BENCHMARK.md and the README table."""

from __future__ import annotations

import argparse
import datetime as dt
import platform
import re
import time
from collections import Counter
from pathlib import Path

from benchmark.generate import FAULTS, FIELDS, generate
from lead_list_qa.qa import check_rows

ROOT = Path(__file__).resolve().parent.parent
CODE = {"dup_email": "dup", "dup_name": "dup"}


def pct(a: int, b: int) -> str:
    return f"{100 * a / b:.1f}%" if b else "n/a"


def run(seed: int, people: int) -> dict[str, object]:
    rows = generate(seed, people)
    start = time.perf_counter()
    results, _ = check_rows(rows, FIELDS)
    seconds = time.perf_counter() - start
    planted: Counter[str] = Counter()
    caught: Counter[str] = Counter()
    clean = flagged = 0
    title_ok = title_n = 0
    for row, r in zip(rows, results, strict=True):
        fault = row["planted_fault"]
        if not fault:
            clean += 1
            flagged += bool(r.issues) or r.duplicate_of is not None
            title_n += 1
            title_ok += r.seniority == row["true_seniority"]
            continue
        planted[fault] += 1
        want = CODE.get(fault, fault)
        caught[fault] += (r.duplicate_of is not None) if want == "dup" else (want in r.codes)
    return {"rows": len(rows), "planted": planted, "caught": caught, "clean": clean,
            "flagged": flagged, "title_ok": title_ok, "title_n": title_n, "seconds": seconds}


def table(s: dict[str, object]) -> str:
    planted: Counter[str] = s["planted"]
    caught: Counter[str] = s["caught"]
    lines = ["| Measure | Result |", "|---|---:|", f"| Rows | {s['rows']:,} |"]
    for f in FAULTS:
        lines.append(f"| Caught: `{f}` | **{pct(caught[f], planted[f])}** "
                     f"({caught[f]} of {planted[f]}) |")
    total_c, total_p = sum(caught.values()), sum(planted.values())
    lines.append(f"| Caught: all planted faults | **{pct(total_c, total_p)}** "
                 f"({total_c:,} of {total_p:,}) |")
    lines.append(f"| Clean rows flagged by mistake | **{pct(s['flagged'], s['clean'])}** "
                 f"({s['flagged']} of {s['clean']:,}) |")
    lines.append(f"| Title bucket right on clean rows | **{pct(s['title_ok'], s['title_n'])}** "
                 f"({s['title_ok']:,} of {s['title_n']:,}) |")
    return "\n".join(lines)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=20261121)
    p.add_argument("--people", type=int, default=5000)
    a = p.parse_args()
    s = run(a.seed, a.people)
    t = table(s)
    md = f"""# Benchmark

Written by `benchmark/run_benchmark.py` on {dt.date.today()} from a real run.
No number on this page was typed by hand.

Command: `python -m benchmark.run_benchmark --seed {a.seed} --people {a.people}`
Python {platform.python_version()} on {platform.system()}.
Checking all {s['rows']:,} rows took {s['seconds']:.2f} s.

## Method

1. Invent {a.people:,} fake contacts: made-up first and last names, made-up companies on
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

{t}

## What this does not show

The faults are planted by the same person who wrote the checks, so the test covers the cases
that were thought of. Real lists have faults nobody planted here: misspelled names, people who
left the company, inboxes that no longer exist. See [LIMITATIONS.md](LIMITATIONS.md).
"""
    (ROOT / "BENCHMARK.md").write_text(md, encoding="utf-8")
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    text = re.sub(r"<!-- benchmark:start -->.*<!-- benchmark:end -->",
                  f"<!-- benchmark:start -->\n{t}\n<!-- benchmark:end -->", text, flags=re.S)
    readme.write_text(text, encoding="utf-8")
    print(t)


if __name__ == "__main__":
    main()
