"""Single-field checks: email, phone, title. Offline, no network calls."""

from __future__ import annotations

import re
from functools import cache
from importlib.resources import files

import phonenumbers

ATOM = r"[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+"
LOCAL_RE = re.compile(rf"^{ATOM}(\.{ATOM})*$")
LABEL_RE = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?$")


@cache
def word_list(name: str) -> frozenset[str]:
    text = files("lead_list_qa").joinpath(f"data/{name}.txt").read_text(encoding="utf-8")
    return frozenset(
        line.strip().lower() for line in text.splitlines() if line.strip() and line[0] != "#"
    )


def email_syntax_issue(email: str) -> str | None:
    """Return why an email fails an RFC-lite syntax check, or None when it passes."""
    if email.count("@") != 1:
        return "email must have exactly one @"
    local, domain = email.split("@")
    if not local or len(local) > 64 or not LOCAL_RE.match(local):
        return "email local part is malformed"
    labels = domain.split(".")
    if len(labels) < 2 or not all(LABEL_RE.match(x) for x in labels):
        return "email domain is malformed"
    if not labels[-1].isalpha() or len(labels[-1]) < 2:
        return "email domain has no valid top-level domain"
    return None


def domain_of(email: str) -> str:
    return email.rsplit("@", 1)[-1].lower()


def is_role(email: str) -> bool:
    local = email.split("@", 1)[0].lower().split("+", 1)[0]
    return local in word_list("role")


def is_freemail(domain: str) -> bool:
    return domain in word_list("freemail")


def is_disposable(domain: str) -> bool:
    return any(domain == d or domain.endswith("." + d) for d in word_list("disposable"))


def site_domain(website: str) -> str:
    """`https://www.Example.com/about` to `example.com`."""
    d = re.sub(r"^[a-z]+://", "", website.strip().lower()).split("/", 1)[0].split(":", 1)[0]
    return d.removeprefix("www.")


def normalize_phone(raw: str, region: str = "US") -> tuple[str | None, str | None]:
    """Return (E.164 number, None) or (None, reason)."""
    try:
        num = phonenumbers.parse(raw, region)
    except phonenumbers.NumberParseException:
        return None, "phone could not be read"
    if not phonenumbers.is_valid_number(num):
        return None, "phone is not a valid number"
    return phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.E164), None


BUCKETS: list[tuple[str, re.Pattern[str]]] = [
    ("VP", re.compile(r"\b(vp|svp|evp|avp|vice president)\b")),
    ("C-level", re.compile(
        r"\b(chief|ceo|cfo|cto|coo|cmo|cio|ciso|cro|president|founder|co-founder|owner)\b")),
    ("Director", re.compile(r"\b(director|head of|dir)\b")),
    ("Manager", re.compile(r"\b(manager|mgr|supervisor|lead)\b")),
]


def title_bucket(title: str) -> str:
    t = re.sub(r"[.,/&]", " ", title.lower())
    if not t.strip():
        return "Unknown"
    return next((name for name, rx in BUCKETS if rx.search(t)), "Staff")
