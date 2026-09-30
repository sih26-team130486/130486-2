# PRAMAAN Frontend — React Web Application
## SIH PS 26190 | Secure Digital Evidence Management System

The frontend provides an intuitive, responsive, and secure interface for investigating officers, forensic analysts, and court officials to interact with digital evidence.

---

## 🚀 Quick Start

### 1. Install Node Dependencies
```bash
npm install
```

### 2. Start the Development Server
```bash
start_frontend.bat
# or
npm run dev
```

Open your browser at: **http://localhost:5173/**

---

## 🔌 Backend Integration & Live Status

The frontend is equipped with a centralized API bridge service ([pramaanApi.js](file:///src/services/pramaanApi.js)) connecting directly to the Django REST Framework backend on `http://127.0.0.1:8000`.

- **Live Backend Status Badge**: Located in the top navigation bar, dynamically indicating:
  - 🟢 **`Backend: Connected`**: Communicating live with the Django server, persisting data to the database, computing server-side cryptographic hashes, and logging to the server audit trail.
  - 🔴 **`Backend: Offline`**: Gracefully falls back to local client-side storage (`localStorage` & `IndexedDB`) so the interface remains fully operational even if the backend is temporarily offline.

---

## 🌟 Key User Workflows

1. **Dashboard & Case Management**:
   - Case overview, evidence statistics, verification ratios, and activity alerts.
2. **Document Upload & Hashing**:
   - Drag-and-drop file upload sending multipart data to `/api/v1/documents/upload/`.
   - Real-time SHA-256 calculation and registration.
3. **Cryptographic Verification**:
   - One-click integrity check calling server `/api/v1/verification/<id>/verify/`.
   - Visual indicators for `VERIFIED` and `TAMPERED` verdicts.
4. **Chain of Custody Tracking**:
   - Visual timeline showing evidence transfers between IO, CFSL, and Court.
5. **PII Detection & Redaction**:
   - Automated identification of Aadhaar, PAN, and contact information.
   - Non-destructive redaction preview.
6. **Legal Certificate Generation**:
   - Triggers server ReportLab PDF creation with diagonal watermark and official serial number.
7. **Multilingual Navigation**:
   - Seamless language switching between English, Hindi (हिंदी), and Marathi (मराठी).

---

## 🛠️ Technical Specifications

- **Framework**: React 18.3 + Vite 6.0
- **Language**: JavaScript (ES Modules)
- **Styling**: Vanilla CSS design system with responsive layouts (Desktop, Tablet, Mobile)
- **State Management**: Reactive runtime state with local caching
- **API Client**: Native `fetch()` with automated JWT bearer authentication header injection
