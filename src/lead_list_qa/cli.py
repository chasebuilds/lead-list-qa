"""Command line: `leadqa check leads.csv -o checked.xlsx`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lead_list_qa.qa import REQUIRED, check_rows
from lead_list_qa.report import read_table, write_report


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="leadqa", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="check a CSV or Excel contact list")
    c.add_argument("file", type=Path)
    c.add_argument("-o", "--out", type=Path, default=Path("leads-checked.xlsx"))
    c.add_argument("--region", default="US", help="default phone region (default US)")
    a = p.parse_args(argv)
    try:
        headers, rows = read_table(a.file)
    except (OSError, UnicodeDecodeError) as e:
        print(f"Could not read {a.file}: {e}", file=sys.stderr)
        return 2
    results, cols = check_rows(rows, headers, a.region)
    missing = [k for k in REQUIRED if k not in cols]
    if missing:
        print(f"No column found for: {', '.join(missing)}", file=sys.stderr)
        return 2
    n = write_report(a.out, headers, results)
    print(f"{n['rows']} rows: {n['clean']} clean, {n['review']} to review, "
          f"{n['duplicates']} duplicates removed")
    print(f"Wrote {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
