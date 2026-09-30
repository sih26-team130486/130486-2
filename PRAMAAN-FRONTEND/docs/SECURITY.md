# PRAMAAN Security Notes

## Security principles

- Never store passwords in plaintext in a production deployment.
- Never expose private keys in the frontend.
- Never rely on hidden frontend controls as authorization.
- Preserve originals; create derivatives for redaction.
- Audit sensitive actions such as upload, download, verify, sign, transfer, approve, redact and export.
- Never silently overwrite evidence or silently resolve custody conflicts.

## Prototype implementation

The demo backend uses Node's `crypto` module for SHA-256 hashing and a JSON persistence file. This is intentionally simple so the package runs without third-party dependencies.

## Production hardening checklist

1. Use an approved identity provider with MFA and Government SSO integration.
2. Enforce RBAC/ABAC at API and data layers.
3. Use encrypted object storage with KMS/HSM-backed keys.
4. Store immutable audit logs in append-only infrastructure.
5. Use signed timestamps and trusted time sources.
6. Use approved digital-signature standards and certificate validation.
7. Add malware scanning and content disarm/reconstruction for uploads.
8. Add API rate limiting, CSRF/session protections and security headers.
9. Use PostgreSQL/Oracle with migrations and encrypted backups.
10. Add real OCR/LLM services with PII-safe processing boundaries.
11. Apply data retention, legal hold and deletion policies.
12. Conduct threat modelling, penetration testing and code signing before deployment.
