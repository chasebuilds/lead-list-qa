import pytest

from lead_list_qa.checks import (
    email_syntax_issue,
    is_disposable,
    is_role,
    normalize_phone,
    site_domain,
    title_bucket,
)


@pytest.mark.parametrize("email", ["a.b@acme.example", "x+tag@sub.acme.example", "o'neil@a.io"])
def test_good_email(email: str) -> None:
    assert email_syntax_issue(email) is None


@pytest.mark.parametrize(
    "email", ["ab.example", "a..b@x.example", "a@x.", "a b@x.example", "a@@x.example", "a@x",
              ".a@x.example", "a@-x.example", "a@x.c0m"],
)
def test_bad_email(email: str) -> None:
    assert email_syntax_issue(email) is not None


def test_role_and_disposable() -> None:
    assert is_role("Sales@acme.example")
    assert is_role("info+web@acme.example")
    assert not is_role("sally@acme.example")
    assert is_disposable("mailinator.com")
    assert is_disposable("x.mailinator.com")
    assert not is_disposable("acme.example")


def test_phone() -> None:
    assert normalize_phone("(212) 555-0142") == ("+12125550142", None)
    assert normalize_phone("+44 20 7946 0958")[0] == "+442079460958"
    assert normalize_phone("555-0142")[1] == "phone is not a valid number"
    assert normalize_phone("call desk")[1] == "phone could not be read"


@pytest.mark.parametrize(
    ("title", "bucket"),
    [("CEO", "C-level"), ("Chief Revenue Officer", "C-level"), ("Vice President, Sales", "VP"),
     ("SVP Marketing", "VP"), ("Head of IT", "Director"), ("Dir. Finance", "Director"),
     ("Office Manager", "Manager"), ("Software Engineer", "Staff"), ("", "Unknown")],
)
def test_title_bucket(title: str, bucket: str) -> None:
    assert title_bucket(title) == bucket


def test_site_domain() -> None:
    assert site_domain("https://www.Acme.example/about") == "acme.example"
