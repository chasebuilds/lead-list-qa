"""Make a fake contact list with planted faults and known answers. Every person is invented."""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path

FIRST = ["Avery", "Bram", "Calla", "Dorian", "Elsie", "Fenn", "Greer", "Hollis", "Ines", "Jory",
         "Kesta", "Lorne", "Mira", "Nolan", "Orla", "Pell", "Quinn", "Rhea", "Soren", "Tamsin",
         "Ulla", "Vance", "Wren", "Xavi", "Yara", "Zeke"]
LAST = ["Ashgrove", "Bellweather", "Corrin", "Dunmore", "Eastlake", "Farrow", "Galloway",
        "Hartwell", "Ivers", "Jessop", "Kittredge", "Lowther", "Marchetti", "Nettleton",
        "Oakhurst", "Pendry", "Quillan", "Rookwood", "Stanhope", "Thackeray", "Underhill",
        "Varga", "Whitlock", "Yardley", "Zoller"]
CO_A = ["Bright", "Copper", "North", "Silver", "Blue", "Granite", "Maple", "Harbor", "Summit",
        "Lumen", "Cedar", "Iron"]
CO_B = ["well", "field", "stone", "gate", "path", "brook", "line", "works", "ridge", "point"]
CO_C = ["Labs", "Systems", "Group", "Partners", "Logistics", "Analytics", "Supply", "Health"]
AREA = ["212", "312", "415", "617", "206", "303", "512", "404", "602", "720"]
TITLES = {
    "C-level": ["CEO", "Chief Financial Officer", "Co-Founder", "CTO", "President"],
    "VP": ["VP of Sales", "Vice President, Operations", "SVP Marketing", "VP Engineering"],
    "Director": ["Director of IT", "Head of Procurement", "Sales Director", "Dir. Finance"],
    "Manager": ["Marketing Manager", "Office Manager", "Team Lead, Support", "Ops Supervisor"],
    "Staff": ["Account Executive", "Data Analyst", "Software Engineer", "Buyer", "Accountant"],
}
FAULTS = ["email_syntax", "role", "disposable", "freemail", "phone", "missing", "dup_email",
          "dup_name"]
FIELDS = ["First Name", "Last Name", "Company", "Title", "Email", "Phone", "Website",
          "planted_fault", "true_seniority"]


def phone(rng: random.Random) -> str:
    a, n = rng.choice(AREA), f"{rng.randint(100, 199):04d}"
    fmt = rng.choice(["({a}) 555-{n}", "{a}-555-{n}", "{a}.555.{n}", "+1 {a} 555 {n}",
                      "1{a}555{n}"])
    return fmt.format(a=a, n=n)


def generate(seed: int, people: int, fault_rate: float = 0.3) -> list[dict[str, str]]:
    rng = random.Random(seed)
    used: set[tuple[str, str, str]] = set()
    rows: list[dict[str, str]] = []
    while len(rows) < people:
        first, last = rng.choice(FIRST), rng.choice(LAST)
        a, b, c = rng.choice(CO_A), rng.choice(CO_B), rng.choice(CO_C)
        company = f"{a}{b} {c}"
        if (first, last, company) in used:
            continue
        used.add((first, last, company))
        dom = f"{(a + b).lower()}-{c.lower()}.example"
        local = rng.choice([f"{first}.{last}", f"{first[0]}{last}", f"{first}"]).lower()
        if local == first.lower():
            local = f"{first}{rng.randint(10, 99)}".lower()
        bucket = rng.choice(list(TITLES))
        rows.append({
            "First Name": first, "Last Name": last, "Company": company,
            "Title": rng.choice(TITLES[bucket]),
            "Email": rng.choice([f"{local}@{dom}", f"{local.title()}@{dom.upper()}"]),
            "Phone": phone(rng), "Website": rng.choice([f"https://www.{dom}", dom, f"{dom}/"]),
            "planted_fault": "", "true_seniority": bucket,
        })
    out: list[dict[str, str]] = []
    for r in rows:
        if rng.random() >= fault_rate or not out:
            out.append(r)
            continue
        fault = rng.choice(FAULTS)
        r = dict(r, planted_fault=fault)
        local, dom = r["Email"].split("@")
        if fault == "email_syntax":
            r["Email"] = rng.choice([f"{local}{dom}", f"{local}..x@{dom}", f"{local}@{dom}.",
                                     f"{local} @{dom}", f"{local}@@{dom}", f"{local}@{dom[:-8]}"])
        elif fault == "role":
            r["Email"] = f"{rng.choice(['info', 'sales', 'contact', 'hello', 'support'])}@{dom}"
        elif fault == "disposable":
            r["Email"] = f"{local}{rng.randint(100, 999)}@" + rng.choice(
                ["mailinator.com", "yopmail.com", "guerrillamail.com", "10minutemail.com"])
        elif fault == "freemail":
            r["Email"] = f"{local}.{rng.randint(1000, 9999)}@" + rng.choice(
                ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com"])
        elif fault == "phone":
            r["Phone"] = rng.choice(["555-0142", "(000) 555-0101", "12345", "call desk",
                                     "212-555-01", "+1 (999) 555-0188"])
        elif fault == "missing":
            r[rng.choice(["First Name", "Last Name", "Company", "Email"])] = ""
        elif fault == "dup_email":
            src = rng.choice([o for o in out if not o["planted_fault"]] or out)
            r = dict(src, Email=f"  {src['Email'].upper()} ", Title=rng.choice(TITLES["Staff"]),
                     planted_fault=fault)
        elif fault == "dup_name":
            src = rng.choice([o for o in out if not o["planted_fault"]] or out)
            sl, sd = src["Email"].split("@")
            r = dict(src, Email=f"{sl}.alt@{sd}", Phone=phone(rng), planted_fault=fault)
            r["First Name"] = src["First Name"].upper()
        out.append(r)
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--people", type=int, default=40)
    p.add_argument("--out", type=Path, default=Path("samples/leads.csv"))
    a = p.parse_args()
    with a.out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        w.writerows(generate(a.seed, a.people))


if __name__ == "__main__":
    main()
