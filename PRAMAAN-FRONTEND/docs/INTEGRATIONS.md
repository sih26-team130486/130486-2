# Integration Notes

The product architecture reserves integration surfaces for:

- CCTNS
- ICJS
- e-Courts
- e-Prisons
- Government SSO
- OCR providers
- LLM/AI providers
- Object storage
- KMS/HSM

No live government API is included or claimed. The UI labels these surfaces as **Integration Ready**, **Prototype**, or **Research** according to the feature status.

Recommended production pattern:

```text
PRAMAAN API
   │
   ├── Identity Adapter ── Government SSO / approved IdP
   ├── Case Adapter ────── CCTNS / ICJS
   ├── Court Adapter ───── e-Courts
   ├── Prison Adapter ──── e-Prisons
   ├── Object Store ────── encrypted evidence objects
   ├── KMS/HSM ─────────── keys and signing
   ├── OCR Service ─────── scanned text
   └── AI Gateway ──────── controlled retrieval + structured outputs
```
