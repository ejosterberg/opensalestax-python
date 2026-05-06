# Security Policy

## Reporting a vulnerability

Email **ejosterberg@gmail.com** with subject line starting
`[opensalestax-python] security:`. Include:

- Affected version(s)
- Reproduction steps
- Expected vs actual behavior
- Suggested mitigation if known

Do not open a public GitHub issue for security reports.

## Response time

Best-effort acknowledgement within 7 days. This is a side project; please
be patient. For critical vulnerabilities affecting production tax
calculations, mark the email subject with `[critical]` and expect faster
turnaround.

## Supported versions

Only the latest minor release receives security patches. There are no
LTS branches. Pin your dependency carefully and read the CHANGELOG
before upgrading.

## Security posture

- TLS verification is enabled by default; disabling it requires an
  explicit `verify=False` argument and emits a `RuntimeWarning`.
- Timeouts are always set; no infinite-hang code paths.
- API keys are sent as `Authorization: Bearer` headers, never in URL
  query strings or request bodies.
- HTTP debug logging at the application level does not include the
  Authorization header by default (httpx's standard behavior).
- Caller-supplied `base_url` values must be validated by the caller —
  the SDK does not perform SSRF mitigation. Connectors built on this
  SDK (e.g. opensalestax-woocommerce, opensalestax-odoo) are
  responsible for validating user-supplied base URLs.
