# PRAMAAN Backend — Django REST Service
## SIH PS 26190 | Secure Digital Evidence Management System

The backend powers the cryptographic integrity pipeline, role-based authorization, custody handovers, legal PDF certificate generation, PII sanitization, and immutable audit logging for PRAMAAN.

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
copy .env.example .env
```
*(By default, SQLite is used for development with pre-configured demo users. To use PostgreSQL, set `USE_POSTGRES=True` in `.env`).*

### 3. Run Migrations & Seed Users
```bash
python manage.py migrate
python manage.py seed_demo
```

### 4. Start the Server
```bash
start_server.bat
# or
python manage.py runserver
```
Backend runs at: **http://127.0.0.1:8000/**  
Django Admin dashboard: **http://127.0.0.1:8000/admin/**

---

## 🔑 Pre-Configured Demo Credentials

| Role | Username | Password |
| :--- | :--- | :--- |
| **ADMIN** | `admin` | `Admin@1234` |
| **IO** | `inspector_sharma` | `IO@12345` |
| **COURT** | `court_user` | `Court@1234` |

---

## 📡 Complete REST API Endpoints

### 1. Authentication (`/api/v1/auth/`)
| Method | URL | Role | Description |
| :---: | :--- | :---: | :--- |
| `POST` | `/api/v1/auth/login/` | Public | Obtain JWT access + refresh tokens |
| `POST` | `/api/v1/auth/refresh/` | Public | Refresh expired access token |
| `POST` | `/api/v1/auth/logout/` | Auth | Blacklist refresh token |
| `POST` | `/api/v1/auth/register/` | Admin | Register new officer account |
| `GET` | `/api/v1/auth/profile/` | Auth | Current user profile details |
| `GET` | `/api/v1/auth/users/` | Admin | List all registered system users |

### 2. Documents & Storage (`/api/v1/documents/`)
| Method | URL | Role | Description |
| :---: | :--- | :---: | :--- |
| `POST` | `/api/v1/documents/upload/` | IO, Admin | Upload file & compute ground-truth SHA-256 |
| `GET` | `/api/v1/documents/` | Auth | List all registered evidence documents |
| `GET` | `/api/v1/documents/{id}/` | Auth | Detailed document metadata & hash |
| `GET` | `/api/v1/documents/{id}/download/`| Auth | Stream evidence file with hash header |
| `DELETE`| `/api/v1/documents/{id}/` | Admin | Securely remove evidence document |

### 3. Verification & Tamper Detection (`/api/v1/verification/`)
| Method | URL | Role | Description |
| :---: | :--- | :---: | :--- |
| `POST` | `/api/v1/verification/{doc_id}/verify/` | IO, Admin | Re-compute hash from disk & compare |
| `GET` | `/api/v1/verification/` | Auth | List all verification records |
| `GET` | `/api/v1/verification/{id}/` | Auth | Detailed verification verdict & hash match |

### 4. Chain of Custody (`/api/v1/custody/`)
| Method | URL | Role | Description |
| :---: | :--- | :---: | :--- |
| `POST` | `/api/v1/custody/` | IO, Admin | Register document into custody chain |
| `GET` | `/api/v1/custody/` | Auth | List all active custody chains |
| `GET` | `/api/v1/custody/{id}/` | Auth | Chain details with current holder & location |
| `POST` | `/api/v1/custody/{id}/transfer/` | IO, Admin | Initiate transfer with hash snapshot |
| `POST` | `/api/v1/custody/transfer/{t_id}/confirm/`| IO, Admin | Recipient confirms receipt of evidence |
| `POST` | `/api/v1/custody/transfer/{t_id}/reject/` | IO, Admin | Recipient rejects custody transfer |
| `GET` | `/api/v1/custody/{id}/history/` | Auth | Chronological transfer timeline |

### 5. Legal Evidence Certificates (`/api/v1/certificates/`)
| Method | URL | Role | Description |
| :---: | :--- | :---: | :--- |
| `POST` | `/api/v1/certificates/generate/` | IO, Admin | Generate official ReportLab PDF certificate |
| `GET` | `/api/v1/certificates/` | Auth | List all generated evidence certificates |
| `GET` | `/api/v1/certificates/{id}/` | Auth | Certificate metadata & PDF checksum |
| `GET` | `/api/v1/certificates/{id}/download/` | Auth | Download verifiable PDF certificate |

### 6. PII Redaction (`/api/v1/redaction/`)
| Method | URL | Role | Description |
| :---: | :--- | :---: | :--- |
| `POST` | `/api/v1/redaction/detect/` | IO, Admin | Scan for Aadhaar, PAN, phone, etc. |
| `POST` | `/api/v1/redaction/redact/` | IO, Admin | Produce sanitized redacted file copy |
| `GET` | `/api/v1/redaction/` | IO, Admin | List all redaction jobs |
| `GET` | `/api/v1/redaction/{id}/` | Auth | Redaction report & detected entity counts |
| `GET` | `/api/v1/redaction/{id}/download/`| Auth | Stream sanitized file copy |

### 7. Multi-Criteria Search (`/api/v1/search/`)
| Method | URL | Role | Description |
| :---: | :--- | :---: | :--- |
| `GET` | `/api/v1/search/documents/` | Auth | Search by `q`, `case_id`, `status`, `hash`, `has_pii`, `has_custody`, `date_from`, `date_to` |

### 8. Audit Logs (`/api/v1/audit/`)
| Method | URL | Role | Description |
| :---: | :--- | :---: | :--- |
| `GET` | `/api/v1/audit/` | IO, Admin | Immutable audit log trail (filterable) |
| `GET` | `/api/v1/audit/stats/` | IO, Admin | Summary counts & tamper alert statistics |
| `GET` | `/api/v1/audit/{id}/` | IO, Admin | Single audit entry details |

---

## 🎬 Automated Demo Scripts

Each phase of the project can be demonstrated with a single command:

- **P0 Flow (Upload ➔ Hash ➔ Verify ➔ Tamper ➔ Alert ➔ Audit)**:
  ```bash
  run_demo.bat
  ```
- **P1 Flow (Chain of Custody ➔ Transfer ➔ Confirm ➔ Legal PDF Certificate)**:
  ```bash
  run_demo_p1.bat
  ```
- **P2 Flow (PII Redaction ➔ Multi-Filter Search ➔ Sanitized Download)**:
  ```bash
  run_demo_p2.bat
  ```
- **Full QA Test Suite (201 Automated Verification Checks)**:
  ```bash
  python -X utf8 qa_full.py
  ```

---

## 🛠️ Technical Specifications

- **Runtime**: Python 3.13
- **Framework**: Django 5.2.1 + Django REST Framework 3.16.1
- **Authentication**: JWT via `djangorestframework-simplejwt`
- **PDF Generation**: ReportLab 5.0.1 + PyMuPDF 1.28.2
- **Database**: SQLite (default dev) / PostgreSQL (production-ready via `.env`)
- **Hashing**: Python standard library `hashlib` (SHA-256)
- **CORS Support**: `django-cors-headers` configured for Vite frontend
