window.DEMO = {
  repo: "lead-list-qa",
  title: "lead-list-qa",
  tagline: "Drop in a CSV or Excel contact list. Phones are checked and formatted, emails and names checked, duplicates removed, and seniority read from job titles. Rows that need a person go to a review sheet with the reason.",
  pkg: "lead_list_qa",
  packages: ["openpyxl", "phonenumbers"],
  inputs: [
    { id: "input", label: "Contact list (CSV or XLSX)", accept: ".csv,.xlsx", sample: "samples/leads.csv" },
  ],
  options: [
    { id: "region", label: "Default phone region", type: "text", value: "US" },
  ],
  sampleNote: 'The sample is <a href="samples/leads.csv">leads.csv</a>: 40 invented contacts on .example domains with 555 phone numbers and planted faults.',
  python: `
from pathlib import Path
from lead_list_qa.cli import main as cli_main

def run(paths, opts):
    src = paths["input"][0]
    out = "/work/" + Path(src).stem + "-checked.xlsx"
    code, log = run_cli(cli_main, ["check", src, "-o", out, "--region", opts.get("region", "").strip() or "US"])
    if code != 0 or not Path(out).exists():
        return {"ok": False, "log": log, "sheets": [], "download": None}
    return {"ok": True, "log": log, "sheets": sheets_from_xlsx(out), "download": out}
`,
};
