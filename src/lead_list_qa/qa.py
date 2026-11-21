"""Row-level checks, duplicate detection and scoring."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from lead_list_qa.checks import (
    domain_of,
    email_syntax_issue,
    is_disposable,
    is_freemail,
    is_role,
    normalize_phone,
    site_domain,
    title_bucket,
)

ALIASES: dict[str, tuple[str, ...]] = {
    "email": ("email", "email address", "e-mail", "work email"),
    "first_name": ("first name", "firstname", "first"),
    "last_name": ("last name", "lastname", "last", "surname"),
    "company": ("company", "company name", "organization", "account", "account name"),
    "title": ("title", "job title", "position"),
    "phone": ("phone", "phone number", "work phone", "direct phone", "mobile"),
    "website": ("website", "company website", "domain", "url"),
}
REQUIRED = ("email", "first_name", "last_name", "company")
PENALTY = {
    "missing": 30, "email_syntax": 60, "disposable": 50, "role": 25, "freemail": 15,
    "domain_mismatch": 10, "phone": 15,
}


@dataclass
class Result:
    row: int
    values: dict[str, str]
    email: str = ""
    phone_e164: str = ""
    seniority: str = "Unknown"
    issues: list[tuple[str, str]] = field(default_factory=list)
    duplicate_of: int | None = None

    @property
    def score(self) -> int:
        return max(0, 100 - sum(PENALTY[code] for code, _ in self.issues))

    @property
    def reasons(self) -> str:
        return "; ".join(text for _, text in self.issues)

    @property
    def codes(self) -> set[str]:
        return {code for code, _ in self.issues}


def map_columns(headers: list[str]) -> dict[str, str]:
    """Map our field names to the file's header names, matching common aliases."""
    norm = {re.sub(r"\s+", " ", h.strip().lower().replace("_", " ")): h for h in headers}
    out: dict[str, str] = {}
    for key, names in ALIASES.items():
        hit = next((norm[n] for n in names if n in norm), None)
        if hit is not None:
            out[key] = hit
    return out


def _email_issues(email: str, website: str) -> list[tuple[str, str]]:
    bad = email_syntax_issue(email)
    if bad:
        return [("email_syntax", bad)]
    out: list[tuple[str, str]] = []
    dom = domain_of(email)
    if is_disposable(dom):
        out.append(("disposable", f"disposable email domain {dom}"))
    if is_role(email):
        out.append(("role", "role address, not a person"))
    site = site_domain(website) if website else ""
    if is_freemail(dom):
        out.append(("freemail", f"free-mail address ({dom}) for a company contact"))
    elif site and dom != site and not dom.endswith("." + site):
        out.append(("domain_mismatch", f"email domain {dom} does not match website {site}"))
    return out


def check_row(row: int, values: dict[str, str], cols: dict[str, str], region: str) -> Result:
    get = {k: (values.get(h) or "").strip() for k, h in cols.items()}
    r = Result(row=row, values=values)
    for k in REQUIRED:
        if not get.get(k):
            r.issues.append(("missing", f"missing {k.replace('_', ' ')}"))
    r.email = get.get("email", "").lower()
    if r.email:
        r.issues += _email_issues(r.email, get.get("website", ""))
    if get.get("phone"):
        e164, why = normalize_phone(get["phone"], region)
        if why:
            r.issues.append(("phone", why))
        r.phone_e164 = e164 or ""
    r.seniority = title_bucket(get.get("title", ""))
    return r


def mark_duplicates(results: list[Result], cols: dict[str, str]) -> None:
    """First row wins. Later rows with the same email, or same name and company, are dupes."""
    seen: dict[tuple[str, ...], int] = {}

    def key(r: Result, k: str) -> str:
        return re.sub(r"[^a-z0-9]", "", (r.values.get(cols.get(k, "")) or "").lower())

    for r in results:
        keys: list[tuple[str, ...]] = []
        if r.email:
            keys.append(("email", r.email))
        name = (key(r, "first_name"), key(r, "last_name"), key(r, "company"))
        if all(name):
            keys.append(("name", *name))
        first = next((seen[k] for k in keys if k in seen), None)
        if first is not None:
            r.duplicate_of = first
            continue
        for k in keys:
            seen[k] = r.row


def check_rows(
    rows: list[dict[str, str]], headers: list[str], region: str = "US"
) -> tuple[list[Result], dict[str, str]]:
    cols = map_columns(headers)
    results = [check_row(i + 2, v, cols, region) for i, v in enumerate(rows)]
    mark_duplicates(results, cols)
    return results, cols
