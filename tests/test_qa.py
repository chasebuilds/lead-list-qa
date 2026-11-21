from lead_list_qa.qa import check_rows, map_columns

H = ["First Name", "Last Name", "Company", "Title", "Email", "Phone", "Website"]


def row(**kw: str) -> dict[str, str]:
    base = {"First Name": "Avery", "Last Name": "Corrin", "Company": "Brightwell Labs",
            "Title": "CTO", "Email": "avery@brightwell.example", "Phone": "212-555-0142",
            "Website": "brightwell.example"}
    return base | kw


def test_map_columns_aliases() -> None:
    cols = map_columns(["first_name", "Surname", "Account Name", "E-mail", "Job Title"])
    assert cols == {"first_name": "first_name", "last_name": "Surname",
                    "company": "Account Name", "email": "E-mail", "title": "Job Title"}


def test_clean_row() -> None:
    (r,), _ = check_rows([row()], H)
    assert r.issues == []
    assert r.score == 100
    assert r.phone_e164 == "+12125550142"
    assert r.seniority == "C-level"


def test_flags_and_score() -> None:
    rows = [row(Email="info@gmail.com", Phone="12345", Company="")]
    (r,), _ = check_rows(rows, H)
    assert r.codes == {"role", "freemail", "phone", "missing"}
    assert r.score == 100 - 25 - 15 - 15 - 30
    assert "missing company" in r.reasons


def test_domain_mismatch_and_subdomain() -> None:
    (a, b), _ = check_rows(
        [row(Email="a@other.example"),
         row(Email="b@mail.brightwell.example", **{"Last Name": "X"})],
        H,
    )
    assert "domain_mismatch" in a.codes
    assert b.issues == []


def test_duplicates() -> None:
    rows = [row(), row(Email=" AVERY@BRIGHTWELL.EXAMPLE ", **{"First Name": "Bram"}),
            row(Email="ac@brightwell.example", **{"First Name": "AVERY"}),
            row(Email="z@brightwell.example", **{"First Name": "Zeke"})]
    results, _ = check_rows(rows, H)
    assert [r.duplicate_of for r in results] == [None, 2, 2, None]
