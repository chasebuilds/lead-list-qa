"""Read CSV or Excel input and write the four-sheet workbook."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font

from lead_list_qa.qa import Result


def read_table(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if path.suffix.lower() in (".xlsx", ".xlsm"):
        ws = load_workbook(path, read_only=True, data_only=True).worksheets[0]
        it = ws.iter_rows(values_only=True)
        headers = [str(h) if h is not None else "" for h in next(it, ())]
        rows = [
            {h: "" if v is None else str(v) for h, v in zip(headers, r, strict=False)}
            for r in it
            if any(v not in (None, "") for v in r)
        ]
        return headers, rows
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = [{k: v or "" for k, v in r.items() if k is not None} for r in reader]
        return list(reader.fieldnames or []), rows


def _sheet(wb: Workbook, title: str, header: list[str], rows: list[list[object]]) -> None:
    ws = wb.create_sheet(title)
    ws.append(header)
    for c in ws[1]:
        c.font = Font(bold=True)
    for r in rows:
        ws.append(r)
    ws.freeze_panes = "A2"


def write_report(path: Path, headers: list[str], results: list[Result]) -> dict[str, int]:
    extra = ["email_normalized", "phone_e164", "seniority", "score"]
    kept = [r for r in results if r.duplicate_of is None]
    clean = [r for r in kept if not r.issues]
    review = [r for r in kept if r.issues]
    dupes = [r for r in results if r.duplicate_of is not None]

    def base(r: Result) -> list[object]:
        return [r.row, *(r.values.get(h, "") for h in headers), r.email, r.phone_e164,
                r.seniority, r.score]

    wb = Workbook()
    wb.remove(wb.active)
    _sheet(wb, "Clean", ["row", *headers, *extra], [base(r) for r in clean])
    _sheet(wb, "Review", ["row", *headers, *extra, "reasons"],
           [[*base(r), r.reasons] for r in sorted(review, key=lambda r: r.score)])
    _sheet(wb, "Removed duplicates", ["row", *headers, "duplicate_of_row"],
           [[r.row, *(r.values.get(h, "") for h in headers), r.duplicate_of] for r in dupes])
    counts = {"rows": len(results), "clean": len(clean), "review": len(review),
              "duplicates": len(dupes)}
    reasons = Counter(code for r in review for code in r.codes)
    buckets = Counter(r.seniority for r in kept)
    summary: list[list[object]] = [[k, v] for k, v in counts.items()]
    summary += [["", ""], ["issue", "rows"], *([k, v] for k, v in reasons.most_common())]
    summary += [["", ""], ["seniority", "rows"], *([k, v] for k, v in buckets.most_common())]
    _sheet(wb, "Summary", ["measure", "value"], summary)
    wb.save(path)
    return counts
