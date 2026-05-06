# Contributing to opensalestax-python

Thank you for considering a contribution.

## Developer Certificate of Origin (DCO)

Every commit must carry a DCO sign-off:

```
git commit -s -m "your message"
```

The `-s` flag appends a `Signed-off-by: Your Name <email>` trailer that
asserts you have the right to submit the contribution under the project
license (Apache 2.0). See [`https://developercertificate.org`](https://developercertificate.org)
for the full text.

PRs without DCO sign-off will be rejected by CI.

## No AI co-author trailers

Do not add `Co-Authored-By:` trailers attributing AI assistants. Human
authors take responsibility for their contributions.

## Code quality

Before opening a PR:

```
ruff check src tests
ruff format --check src tests
mypy --strict src/opensalestax
pytest --cov=opensalestax --cov-fail-under=90
```

CI runs all four on every PR.

## License

By contributing, you agree your contribution is licensed under
Apache 2.0 (the project license).

## Reporting security issues

See [`SECURITY.md`](SECURITY.md). Don't open public issues for
security reports.
