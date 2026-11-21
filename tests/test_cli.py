from pathlib import Path

from openpyxl import load_workbook

from benchmark.generate import FIELDS, generate
from benchmark.run_benchmark import run
from lead_list_qa.cli import main

SAMPLE = Path(__file__).resolve().parent.parent / "samples" / "leads.csv"


def test_cli_writes_four_sheets(tmp_path: Path, capsys: object) -> None:
    out = tmp_path / "checked.xlsx"
    assert main(["check", str(SAMPLE), "-o", str(out)]) == 0
    wb = load_workbook(out)
    assert wb.sheetnames == ["Clean", "Review", "Removed duplicates", "Summary"]
    assert wb["Review"].cell(1, wb["Review"].max_column).value == "reasons"


def test_cli_xlsx_input_and_bad_columns(tmp_path: Path) -> None:
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.append(["Email", "First", "Last", "Company"])
    ws.append(["a@b.example", "A", "B", "C"])
    src = tmp_path / "in.xlsx"
    wb.save(src)
    assert main(["check", str(src), "-o", str(tmp_path / "o.xlsx")]) == 0
    bad = tmp_path / "bad.csv"
    bad.write_text("Name,Phone\nx,1\n", encoding="utf-8")
    assert main(["check", str(bad), "-o", str(tmp_path / "o2.xlsx")]) == 2
    assert main(["check", str(tmp_path / "nope.csv")]) == 2


def test_benchmark_small_run() -> None:
    rows = generate(3, 300)
    assert set(rows[0]) == set(FIELDS)
    s = run(3, 300)
    assert s["flagged"] == 0
    assert s["title_ok"] == s["title_n"]
