# Limitations

## It does not prove an inbox exists

This is the main one. A row that passes every check can still bounce. The tool never contacts a
mail server, never looks up MX records and never sends anything, so it cannot tell whether
`jane.doe@acme.example` is a real mailbox, a catch-all, a person who left last year, or a typo of
a real address. It checks format and patterns only. To know whether an inbox exists you need a
verification service or a real send, and both are out of scope on purpose.

## Other limits

- **Email syntax is RFC-lite.** Quoted local parts (`"john doe"@x.com`), IP-address domains and
  non-ASCII (internationalized) addresses are rejected even though the standard allows them. They
  are rare in B2B lists, and a rejected row goes to Review, not away.
- **The domain lists are small.** The disposable list has about a dozen domains, the free-mail
  list about 16, the role list about 20 local parts. New throwaway domains appear daily and will
  pass. Edit the files in `src/lead_list_qa/data/` to add more.
- **Free-mail is always flagged.** A real owner of a small business who uses Gmail gets a review
  reason. That is a choice: on a B2B list it is worth a look, not an automatic removal.
- **Website match is exact.** `acme.example` and `mail.acme.example` match. A company that mails
  from a different brand domain (`acmecorp.example` vs website `acme.example`) is flagged.
- **Phone validity is format only.** `phonenumbers` knows which number ranges exist in each
  country. It cannot tell whether a number is in service or reaches the person. Numbers without a
  `+` country code are read as US unless you pass `--region`.
- **Duplicates need an exact match** after trimming and case folding: the same email, or the same
  first name, last name and company with punctuation removed. `Bob` vs `Robert`, or `Acme Inc` vs
  `Acme Incorporated`, are not matched. There is no fuzzy matching.
- **Title buckets are keyword rules.** `President` is C-level, so a `Regional President` lands
  there too. `Lead` means Manager, so `Lead Engineer` is Manager, not Staff. Titles in other
  languages mostly fall to Staff.
- **The benchmark uses planted faults.** The same rules that made the faults are the ones the
  checks look for, so the catch rates mostly show the checks work as written. See
  [BENCHMARK.md](BENCHMARK.md).
