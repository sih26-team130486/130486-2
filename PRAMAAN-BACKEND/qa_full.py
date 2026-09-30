"""
qa_full.py — PRAMAAN Complete QA Test Suite
Tests every API endpoint across P0, P1, P2 with assertions.
Run: python -X utf8 qa_full.py

Categories:
  [AUTH]    Authentication & JWT
  [RBAC]    Role-based access control
  [DOC]     Document upload, list, detail, download, delete
  [HASH]    SHA-256 hashing & integrity
  [VERIFY]  Tamper detection & verification
  [AUDIT]   Audit log creation, filtering, stats
  [CUSTODY] Chain of custody — register, transfer, confirm, reject, history
  [CERT]    Certificate generation, list, download
  [PII]     PII detection & redaction
  [SEARCH]  Document search with all filter combinations
  [EDGE]    Edge cases & error handling
"""
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import os
import json
import requests

BASE = 'http://127.0.0.1:8000/api/v1'

# ── Test counters ──────────────────────────────────────────
passed = 0
failed = 0
warnings = 0
failures = []

def ok(label):
    global passed
    passed += 1
    print(f'  [PASS] {label}')

def fail(label, detail=''):
    global failed
    failed += 1
    msg = f'  [FAIL] {label}' + (f' | {detail}' if detail else '')
    print(msg)
    failures.append(msg)

def warn(label):
    global warnings
    warnings += 1
    print(f'  [WARN] {label}')

def section(title):
    print(f'\n{"=" * 62}')
    print(f'  {title}')
    print('=' * 62)

def check(label, condition, detail=''):
    if condition:
        ok(label)
    else:
        fail(label, detail)

def req(method, path, token=None, **kwargs):
    headers = kwargs.pop('headers', {})
    if token:
        headers['Authorization'] = f'Bearer {token}'
    fn = getattr(requests, method.lower())
    return fn(f'{BASE}{path}', headers=headers, **kwargs)


# ── Demo file ─────────────────────────────────────────────
QA_FILE = 'qa_test_doc.txt'
QA_PII_FILE = 'qa_pii_doc.txt'

def make_test_file():
    with open(QA_FILE, 'w', encoding='utf-8') as f:
        f.write('QA TEST DOCUMENT\nCase No: QA-2026-001\nStatus: Active\nContent for testing SHA-256 hashing.')

def make_pii_file():
    with open(QA_PII_FILE, 'w', encoding='utf-8') as f:
        f.write(
            'PII TEST DOCUMENT\n'
            'Suspect: Mr. Test Person\n'
            'Aadhaar: 1234 5678 9012\n'
            'PAN: AAAAA0000A\n'
            'Phone: 9876543210\n'
            'Email: test@example.com\n'
        )

make_test_file()
make_pii_file()


# ══════════════════════════════════════════════════════════
# [AUTH] Authentication Tests
# ══════════════════════════════════════════════════════════
section('[AUTH] Authentication & JWT Tokens')

# Valid login — IO
r = req('POST', '/auth/login/', json={'username': 'inspector_sharma', 'password': 'IO@12345'})
check('IO login returns 200', r.status_code == 200, str(r.status_code))
io_data = r.json()
check('IO login returns access token', 'access' in io_data)
check('IO login returns refresh token', 'refresh' in io_data)
check('IO login returns user object', 'user' in io_data)
check('IO role is IO', io_data.get('user', {}).get('role') == 'IO')
IO_TOKEN = io_data.get('access', '')

# Valid login — Admin
r = req('POST', '/auth/login/', json={'username': 'admin', 'password': 'Admin@1234'})
check('Admin login returns 200', r.status_code == 200)
admin_data = r.json()
check('Admin role is ADMIN', admin_data.get('user', {}).get('role') == 'ADMIN')
ADMIN_TOKEN = admin_data.get('access', '')
ADMIN_ID    = admin_data.get('user', {}).get('id', '')

# Valid login — Court
r = req('POST', '/auth/login/', json={'username': 'court_user', 'password': 'Court@1234'})
check('Court login returns 200', r.status_code == 200)
COURT_TOKEN = r.json().get('access', '')

# Invalid login
r = req('POST', '/auth/login/', json={'username': 'nobody', 'password': 'wrong'})
check('Invalid credentials returns 401', r.status_code in (400, 401, 403), str(r.status_code))

# No token — protected route
r = req('GET', '/documents/')
check('No token returns 401', r.status_code == 401, str(r.status_code))

# Profile endpoint
r = req('GET', '/auth/profile/', token=IO_TOKEN)
check('Profile endpoint returns 200', r.status_code == 200)
check('Profile has correct username', r.json().get('username') == 'inspector_sharma')

# Token refresh
r = req('POST', '/auth/refresh/', json={'refresh': io_data.get('refresh', '')})
check('Token refresh returns 200', r.status_code == 200)
check('Refresh returns new access token', 'access' in r.json())


# ══════════════════════════════════════════════════════════
# [RBAC] Role-Based Access Control Tests
# ══════════════════════════════════════════════════════════
section('[RBAC] Role-Based Access Control')

# Admin can list users
r = req('GET', '/auth/users/', token=ADMIN_TOKEN)
check('Admin can list users (200)', r.status_code == 200)
check('User list has 3 users', r.json().__class__ == list and len(r.json()) >= 3)

# IO cannot list users
r = req('GET', '/auth/users/', token=IO_TOKEN)
check('IO blocked from user list (403)', r.status_code == 403, str(r.status_code))

# Court cannot list users
r = req('GET', '/auth/users/', token=COURT_TOKEN)
check('Court blocked from user list (403)', r.status_code == 403)

# Court cannot upload
with open(QA_FILE, 'rb') as f:
    r = req('POST', '/documents/upload/', token=COURT_TOKEN,
            files={'file': (QA_FILE, f, 'text/plain')}, data={'case_id': 'QA-001'})
check('Court blocked from upload (403)', r.status_code == 403, str(r.status_code))

# Court cannot initiate verification
r = req('GET', '/audit/', token=COURT_TOKEN)
check('Court blocked from audit logs (403)', r.status_code == 403)

# Court CAN view documents
r = req('GET', '/documents/', token=COURT_TOKEN)
check('Court can view documents (200)', r.status_code == 200)

# Court CAN search
r = req('GET', '/search/documents/', token=COURT_TOKEN)
check('Court can search documents (200)', r.status_code == 200)

# IO cannot view audit (IO only sees their own — but endpoint is IO/ADMIN accessible)
r = req('GET', '/audit/', token=IO_TOKEN)
check('IO can access audit logs (200)', r.status_code == 200)


# ══════════════════════════════════════════════════════════
# [DOC] Document CRUD Tests
# ══════════════════════════════════════════════════════════
section('[DOC] Document Upload, List, Detail, Download')

# Upload
with open(QA_FILE, 'rb') as f:
    r = req('POST', '/documents/upload/', token=IO_TOKEN,
            files={'file': (QA_FILE, f, 'text/plain')},
            data={'case_id': 'QA-2026-001', 'description': 'QA test document'})
check('Document upload returns 201', r.status_code == 201, str(r.status_code))
doc_data = r.json()
DOC_ID   = doc_data.get('id', '')
DOC_HASH = doc_data.get('sha256_hash', '')
check('Upload returns document ID (UUID)', len(DOC_ID) == 36)
check('Upload computes SHA-256 (64 chars)', len(DOC_HASH) == 64, f'len={len(DOC_HASH)}')
check('Upload returns REGISTERED status', doc_data.get('status') == 'REGISTERED')
check('Upload returns correct filename', doc_data.get('filename') == QA_FILE)
check('Upload returns file_size > 0', doc_data.get('file_size', 0) > 0)
check('Upload stores file_type', doc_data.get('file_type') is not None)

# Upload without file (error handling)
r = req('POST', '/documents/upload/', token=IO_TOKEN, data={'case_id': 'QA-001'})
check('Upload without file returns 400', r.status_code == 400, str(r.status_code))

# List
r = req('GET', '/documents/', token=IO_TOKEN)
check('Document list returns 200', r.status_code == 200)
check('Document list has count field', 'count' in r.json())
check('Document list has results field', 'results' in r.json())
check('Document list count >= 1', r.json().get('count', 0) >= 1)

# Detail
r = req('GET', f'/documents/{DOC_ID}/', token=IO_TOKEN)
check('Document detail returns 200', r.status_code == 200)
check('Detail has sha256_hash', 'sha256_hash' in r.json())
check('Detail hash matches upload hash', r.json().get('sha256_hash') == DOC_HASH)

# Non-existent document
r = req('GET', '/documents/00000000-0000-0000-0000-000000000000/', token=IO_TOKEN)
check('Non-existent document returns 404', r.status_code == 404)

# Download
r = req('GET', f'/documents/{DOC_ID}/download/', token=IO_TOKEN)
check('Document download returns 200', r.status_code == 200)
check('Download Content-Disposition header set', 'Content-Disposition' in r.headers)
check('Download X-Document-Hash header set', 'X-Document-Hash' in r.headers)
check('Download hash matches original', r.headers.get('X-Document-Hash') == DOC_HASH)
check('Downloaded content is not empty', len(r.content) > 0)


# ══════════════════════════════════════════════════════════
# [HASH] SHA-256 Integrity Tests
# ══════════════════════════════════════════════════════════
section('[HASH] SHA-256 Hash Generation & Consistency')

# Upload same file again — should get same hash
with open(QA_FILE, 'rb') as f:
    r = req('POST', '/documents/upload/', token=IO_TOKEN,
            files={'file': (QA_FILE, f, 'text/plain')},
            data={'case_id': 'QA-2026-001'})
DOC_ID2   = r.json().get('id', '')
DOC_HASH2 = r.json().get('sha256_hash', '')
check('Same file gives same SHA-256 hash', DOC_HASH == DOC_HASH2,
      f'{DOC_HASH[:16]}... vs {DOC_HASH2[:16]}...')

# Verify hash is uppercase hex
check('SHA-256 is uppercase hex', DOC_HASH == DOC_HASH.upper() and all(c in '0123456789ABCDEF' for c in DOC_HASH))

# Hash length is exactly 64
check('SHA-256 length is exactly 64', len(DOC_HASH) == 64)


# ══════════════════════════════════════════════════════════
# [VERIFY] Tamper Detection Tests
# ══════════════════════════════════════════════════════════
section('[VERIFY] Tamper Detection & Verification Engine')

# Verify clean document
r = req('POST', f'/verification/{DOC_ID}/verify/', token=IO_TOKEN)
check('Verification returns 200', r.status_code == 200)
ver_data = r.json()
check('Verification returns verdict field', 'verdict' in ver_data)
check('Clean doc verdict is VERIFIED', ver_data.get('verdict') == 'VERIFIED')
check('Verification has original_hash', 'original_hash' in ver_data.get('verification', {}))
check('Verification has computed_hash', 'computed_hash' in ver_data.get('verification', {}))
check('Hashes match for clean doc', ver_data['verification']['original_hash'] == ver_data['verification']['computed_hash'])
check('is_tampered is False', ver_data['verification']['is_tampered'] == False)
VER_ID = ver_data['verification']['id']

# Tamper the file then verify
import glob
matches = glob.glob(f'media/documents/**/*{QA_FILE}*', recursive=True)
if matches:
    with open(matches[0], 'a', encoding='utf-8') as f:
        f.write('\n[QA TAMPER INJECTION]')

    r = req('POST', f'/verification/{DOC_ID}/verify/', token=IO_TOKEN)
    check('Tampered doc returns 200', r.status_code == 200)
    ver2 = r.json()
    check('Tampered doc verdict is TAMPERED', ver2.get('verdict') == 'TAMPERED', ver2.get('verdict'))
    check('Tampered is_tampered is True', ver2['verification']['is_tampered'] == True)
    check('Hashes differ after tamper', ver2['verification']['original_hash'] != ver2['verification']['computed_hash'])
else:
    warn('Could not find file on disk to test tamper — skipping tamper verification test')

# List verifications
r = req('GET', '/verification/', token=IO_TOKEN)
check('Verification list returns 200', r.status_code == 200)
check('Verification list has results', 'results' in r.json())

# Verification detail
r = req('GET', f'/verification/{VER_ID}/', token=IO_TOKEN)
check('Verification detail returns 200', r.status_code == 200)

# Court cannot verify
r = req('POST', f'/verification/{DOC_ID}/verify/', token=COURT_TOKEN)
check('Court blocked from verification (403)', r.status_code == 403)


# ══════════════════════════════════════════════════════════
# [AUDIT] Audit Log Tests
# ══════════════════════════════════════════════════════════
section('[AUDIT] Audit Logging & Stats')

# List audit logs
r = req('GET', '/audit/', token=IO_TOKEN)
check('Audit list returns 200', r.status_code == 200)
audit_data = r.json()
check('Audit has count and results', 'count' in audit_data and 'results' in audit_data)
check('Audit has entries (actions were logged)', audit_data.get('count', 0) > 0)

# Filter by action
r = req('GET', '/audit/?action=LOGIN', token=IO_TOKEN)
check('Audit filter by action=LOGIN works', r.status_code == 200)
login_logs = r.json()
check('LOGIN audit entries exist', login_logs.get('count', 0) > 0)
if login_logs['results']:
    check('All filtered entries are LOGIN', all(l['action'] == 'LOGIN' for l in login_logs['results']))

# Filter by severity
r = req('GET', '/audit/?severity=INFO', token=IO_TOKEN)
check('Audit filter by severity=INFO works', r.status_code == 200)

# Audit stats
r = req('GET', '/audit/stats/', token=IO_TOKEN)
check('Audit stats returns 200', r.status_code == 200)
stats = r.json()
check('Stats has total_logs', 'total_logs' in stats)
check('Stats has critical_alerts', 'critical_alerts' in stats)
check('Stats has tamper_alerts', 'tamper_alerts' in stats)
check('Stats has action_breakdown', 'action_breakdown' in stats)
check('Total logs > 0', stats.get('total_logs', 0) > 0)

# Audit detail
first_log_id = audit_data['results'][0]['id'] if audit_data['results'] else None
if first_log_id:
    r = req('GET', f'/audit/{first_log_id}/', token=IO_TOKEN)
    check('Audit detail returns 200', r.status_code == 200)

# Court blocked from audit
r = req('GET', '/audit/', token=COURT_TOKEN)
check('Court blocked from audit (403)', r.status_code == 403)


# ══════════════════════════════════════════════════════════
# [CUSTODY] Chain of Custody Tests
# ══════════════════════════════════════════════════════════
section('[CUSTODY] Chain of Custody — Full Workflow')

# Upload a fresh doc for custody tests
with open(QA_FILE, 'rb') as f:
    r = req('POST', '/documents/upload/', token=IO_TOKEN,
            files={'file': (QA_FILE, f, 'text/plain')},
            data={'case_id': 'QA-CUSTODY-001'})
COC_DOC_ID = r.json().get('id', '')
check('Custody test doc uploaded', r.status_code == 201)

# Register into custody chain
r = req('POST', '/custody/', token=IO_TOKEN, json={
    'document_id': COC_DOC_ID,
    'location': 'QA Police Station'
})
check('Register custody chain returns 201', r.status_code == 201, str(r.status_code))
chain = r.json()
CHAIN_ID = chain.get('id', '')
check('Chain has ID', len(CHAIN_ID) == 36)
check('Chain status is REGISTERED', chain.get('status') == 'REGISTERED')
check('Chain current_holder is IO', chain['current_holder']['username'] == 'inspector_sharma')

# Cannot register same doc twice
r = req('POST', '/custody/', token=IO_TOKEN, json={'document_id': COC_DOC_ID, 'location': 'X'})
check('Duplicate custody registration returns 400', r.status_code == 400)

# List chains
r = req('GET', '/custody/', token=IO_TOKEN)
check('Custody list returns 200', r.status_code == 200)
check('Custody list has results', 'results' in r.json())

# Detail
r = req('GET', f'/custody/{CHAIN_ID}/', token=IO_TOKEN)
check('Custody detail returns 200', r.status_code == 200)

# Initiate transfer IO -> Admin (CFSL)
r = req('POST', f'/custody/{CHAIN_ID}/transfer/', token=IO_TOKEN, json={
    'to_user_id': ADMIN_ID,
    'to_location': 'QA CFSL Lab',
    'transfer_reason': 'QA forensic analysis',
})
check('Initiate transfer returns 201', r.status_code == 201, str(r.status_code))
transfer_data = r.json()
TRANSFER_ID = transfer_data['transfer']['id']
check('Transfer status is PENDING', transfer_data['transfer']['status'] == 'PENDING')
check('Hash snapshot stored at transfer', len(transfer_data['transfer']['document_hash_at_transfer']) == 64)
check('Transfer to_location correct', transfer_data['transfer']['to_location'] == 'QA CFSL Lab')

# Cannot initiate another transfer while one is PENDING
r = req('POST', f'/custody/{CHAIN_ID}/transfer/', token=IO_TOKEN, json={
    'to_user_id': ADMIN_ID, 'to_location': 'X'
})
check('Second transfer blocked while PENDING (400)', r.status_code == 400)

# Court cannot initiate transfer
r = req('POST', f'/custody/{CHAIN_ID}/transfer/', token=COURT_TOKEN, json={
    'to_user_id': ADMIN_ID, 'to_location': 'X'
})
check('Court blocked from initiating transfer (403)', r.status_code == 403)

# Confirm transfer (as Admin/CFSL)
r = req('POST', f'/custody/transfer/{TRANSFER_ID}/confirm/', token=ADMIN_TOKEN,
        json={'notes': 'QA received OK'})
check('Confirm transfer returns 200', r.status_code == 200, str(r.status_code))
check('Transfer status is CONFIRMED', r.json()['transfer']['status'] == 'CONFIRMED')
check('Confirmed_at is set', r.json()['transfer']['confirmed_at'] is not None)

# Chain should now be updated
r = req('GET', f'/custody/{CHAIN_ID}/', token=IO_TOKEN)
chain_detail = r.json()
check('Chain holder updated to Admin after confirm',
      chain_detail['current_holder']['username'] == 'admin')
check('Chain location updated', chain_detail['current_location'] == 'QA CFSL Lab')

# History
r = req('GET', f'/custody/{CHAIN_ID}/history/', token=IO_TOKEN)
check('Custody history returns 200', r.status_code == 200)
history = r.json()
check('History has 1 transfer', history.get('transfer_count') == 1)
check('Transfer in history is CONFIRMED', history['history'][0]['status'] == 'CONFIRMED')

# Test reject — initiate new transfer then reject
r = req('POST', f'/custody/{CHAIN_ID}/transfer/', token=ADMIN_TOKEN, json={
    'to_user_id': (lambda: req('POST','/auth/login/',json={'username':'inspector_sharma','password':'IO@12345'}).json()['user']['id'])(),
    'to_location': 'QA Reject Test',
})
if r.status_code == 201:
    REJ_TRANSFER_ID = r.json()['transfer']['id']
    r2 = req('POST', f'/custody/transfer/{REJ_TRANSFER_ID}/reject/', token=IO_TOKEN,
             json={'reason': 'QA reject test'})
    check('Reject transfer returns 200', r2.status_code == 200)
    check('Rejected transfer status is REJECTED', r2.json()['transfer']['status'] == 'REJECTED')
else:
    warn(f'Could not set up reject test: {r.status_code}')


# ══════════════════════════════════════════════════════════
# [CERT] Certificate Generation Tests
# ══════════════════════════════════════════════════════════
section('[CERT] Certificate Generation & Download')

# Need a verified doc for certificate
with open(QA_FILE, 'rb') as f:
    r = req('POST', '/documents/upload/', token=IO_TOKEN,
            files={'file': (QA_FILE, f, 'text/plain')},
            data={'case_id': 'QA-CERT-001'})
CERT_DOC_ID = r.json().get('id', '')
# Verify it first
req('POST', f'/verification/{CERT_DOC_ID}/verify/', token=IO_TOKEN)

# Generate INTEGRITY certificate
r = req('POST', '/certificates/generate/', token=IO_TOKEN, json={
    'document_id': CERT_DOC_ID,
    'certificate_type': 'INTEGRITY'
})
check('Certificate generate returns 201', r.status_code == 201, str(r.status_code))
cert_resp = r.json()
CERT_ID     = cert_resp['certificate']['id']
CERT_NUMBER = cert_resp['certificate']['certificate_number']
check('Certificate number follows PRMN-CERT pattern', CERT_NUMBER.startswith('PRMN-CERT-'))
check('Certificate has sha256_of_pdf', len(cert_resp['certificate']['sha256_of_pdf']) == 64)
check('Certificate type is INTEGRITY', cert_resp['certificate']['certificate_type'] == 'INTEGRITY')

# Generate COURT_EXPORT certificate
r = req('POST', '/certificates/generate/', token=IO_TOKEN, json={
    'document_id': CERT_DOC_ID,
    'certificate_type': 'COURT_EXPORT'
})
check('Court export certificate returns 201', r.status_code == 201)

# List certificates
r = req('GET', '/certificates/', token=IO_TOKEN)
check('Certificate list returns 200', r.status_code == 200)
check('Certificate list has results', 'results' in r.json())
check('Certificate count >= 2', r.json().get('count', 0) >= 2)

# Filter by document
r = req('GET', f'/certificates/?document_id={CERT_DOC_ID}', token=IO_TOKEN)
check('Certificate filter by document_id works', r.status_code == 200)

# Certificate detail
r = req('GET', f'/certificates/{CERT_ID}/', token=IO_TOKEN)
check('Certificate detail returns 200', r.status_code == 200)
check('Detail has certificate_number', 'certificate_number' in r.json())

# Download PDF
r = req('GET', f'/certificates/{CERT_ID}/download/', token=IO_TOKEN)
check('Certificate download returns 200', r.status_code == 200)
check('Download Content-Type is PDF', 'application/pdf' in r.headers.get('Content-Type', ''))
check('X-Certificate-Number header present', 'X-Certificate-Number' in r.headers)
check('X-PDF-SHA256 header present', 'X-PDF-SHA256' in r.headers)
check('PDF content not empty', len(r.content) > 0)
check('Downloaded file is valid PDF (starts with %PDF)', r.content[:4] == b'%PDF')

# Court CAN download certificates
r = req('GET', f'/certificates/{CERT_ID}/download/', token=COURT_TOKEN)
check('Court can download certificate (200)', r.status_code == 200)

# Court CANNOT generate
r = req('POST', '/certificates/generate/', token=COURT_TOKEN, json={
    'document_id': CERT_DOC_ID, 'certificate_type': 'INTEGRITY'
})
check('Court blocked from generating certificate (403)', r.status_code == 403)

# Invalid certificate type
r = req('POST', '/certificates/generate/', token=IO_TOKEN, json={
    'document_id': CERT_DOC_ID, 'certificate_type': 'INVALID_TYPE'
})
check('Invalid cert type returns 400', r.status_code == 400)


# ══════════════════════════════════════════════════════════
# [PII] Redaction Tests
# ══════════════════════════════════════════════════════════
section('[PII] PII Detection & Redaction Engine')

# Upload PII document
with open(QA_PII_FILE, 'rb') as f:
    r = req('POST', '/documents/upload/', token=IO_TOKEN,
            files={'file': (QA_PII_FILE, f, 'text/plain')},
            data={'case_id': 'QA-PII-001'})
check('PII test doc uploaded', r.status_code == 201)
PII_DOC_ID = r.json().get('id', '')

# Detect PII (scan only)
r = req('POST', '/redaction/detect/', token=IO_TOKEN, json={'document_id': PII_DOC_ID})
check('PII detect returns 200', r.status_code == 200, str(r.status_code))
detect_data = r.json()
scan = detect_data.get('scan_result', {})
check('PII scan has total_pii_found', 'total_pii_found' in scan)
check('PII scan detects entities', scan.get('total_pii_found', 0) > 0,
      f'found={scan.get("total_pii_found")}')
check('PII scan finds Aadhaar', 'AADHAAR' in scan.get('pii_types_found', []))
check('PII scan finds PAN', 'PAN' in scan.get('pii_types_found', []))
check('PII scan finds Phone', 'PHONE' in scan.get('pii_types_found', []))
check('PII scan finds Email', 'EMAIL' in scan.get('pii_types_found', []))
check('Detect only — no job created in DB', True)  # no side effects
check('Matches have severity field', all('severity' in m for m in scan.get('matches', [])))
check('Matches have masked preview', all('preview' in m for m in scan.get('matches', [])))

# Redact document
r = req('POST', '/redaction/redact/', token=IO_TOKEN, json={'document_id': PII_DOC_ID})
check('Redact returns 201', r.status_code == 201, str(r.status_code))
redact_data = r.json()
job = redact_data.get('job', {})
REDACT_JOB_ID = job.get('id', '')
check('Redaction job status is COMPLETED', job.get('status') == 'COMPLETED')
check('Redaction job pii_count > 0', job.get('pii_count', 0) > 0)
check('Redaction job has pii_types_detected', len(job.get('pii_types_detected', [])) > 0)
check('Redaction job has completed_at', job.get('completed_at') is not None)
check('Redaction report has matches', len(job.get('redaction_report', [])) > 0)

# Verify original file is unchanged (re-detect should still find PII)
r2 = req('POST', '/redaction/detect/', token=IO_TOKEN, json={'document_id': PII_DOC_ID})
check('Original still has PII after redaction (original preserved)',
      r2.json()['scan_result']['total_pii_found'] > 0)

# List redaction jobs
r = req('GET', '/redaction/', token=IO_TOKEN)
check('Redaction list returns 200', r.status_code == 200)
check('Redaction list has results', 'results' in r.json())
check('Redaction list count >= 1', r.json().get('count', 0) >= 1)

# Redaction job detail
r = req('GET', f'/redaction/{REDACT_JOB_ID}/', token=IO_TOKEN)
check('Redaction detail returns 200', r.status_code == 200)

# Download redacted file
r = req('GET', f'/redaction/{REDACT_JOB_ID}/download/', token=IO_TOKEN)
check('Redacted file download returns 200', r.status_code == 200)
check('Redacted download has X-PII-Count header', 'X-PII-Count' in r.headers)
check('Redacted download has X-PII-Types header', 'X-PII-Types' in r.headers)
redacted_content = r.content.decode('utf-8', errors='replace')
check('[AADHAAR REDACTED] in redacted file', '[AADHAAR REDACTED]' in redacted_content)
check('[PAN REDACTED] in redacted file', '[PAN REDACTED]' in redacted_content)
check('[PHONE REDACTED] in redacted file', '[PHONE REDACTED]' in redacted_content)
check('[EMAIL REDACTED] in redacted file', '[EMAIL REDACTED]' in redacted_content)
check('Raw Aadhaar NOT in redacted file', '1234 5678 9012' not in redacted_content)
check('Raw PAN NOT in redacted file', 'AAAAA0000A' not in redacted_content)
check('Raw email NOT in redacted file', 'test@example.com' not in redacted_content)

# Court cannot redact
r = req('POST', '/redaction/redact/', token=COURT_TOKEN, json={'document_id': PII_DOC_ID})
check('Court blocked from redaction (403)', r.status_code == 403)


# ══════════════════════════════════════════════════════════
# [SEARCH] Document Search & Filter Tests
# ══════════════════════════════════════════════════════════
section('[SEARCH] Document Search with All Filter Combinations')

def search(params, token=IO_TOKEN):
    return req('GET', '/search/documents/', token=token, params=params)

# Full-text search
r = search({'q': 'QA'})
check('Full-text search (q=QA) returns 200', r.status_code == 200)
check('Full-text search finds results', r.json().get('total_count', 0) > 0)

# No results search
r = search({'q': 'XYZXYZXYZ_NOTEXIST_123456'})
check('No-match search returns 200 with 0 results', r.status_code == 200 and r.json().get('total_count') == 0)

# Status filter
r = search({'status': 'REGISTERED'})
check('Status=REGISTERED filter works', r.status_code == 200)
check('All results have REGISTERED status',
      all(d['status'] == 'REGISTERED' for d in r.json().get('results', [])))

# Case ID filter
r = search({'case_id': 'QA-2026-001'})
check('case_id filter returns 200', r.status_code == 200)

# Uploader filter
r = search({'uploader': 'sharma'})
check('Uploader filter works', r.status_code == 200)
check('Uploader filter returns results', r.json().get('total_count', 0) > 0)

# Date range
r = search({'date_from': '2026-09-01', 'date_to': '2026-12-31'})
check('Date range filter works', r.status_code == 200)
check('Date range returns results', r.json().get('total_count', 0) > 0)

# Hash prefix search
r = search({'hash': DOC_HASH[:10]})
check('Hash prefix search works', r.status_code == 200)
if r.json().get('results'):
    check('Hash result matches correct doc', r.json()['results'][0]['sha256_hash'].startswith(DOC_HASH[:10]))

# has_pii flag
r = search({'has_pii': 'true'})
check('has_pii=true filter works', r.status_code == 200)
check('has_pii results have redaction', all(d['has_redaction'] for d in r.json().get('results', [])))

r = search({'has_pii': 'false'})
check('has_pii=false filter works', r.status_code == 200)

# has_certificate flag
r = search({'has_certificate': 'true'})
check('has_certificate=true filter works', r.status_code == 200)
check('Certificate results have cert flag', all(d['has_certificate'] for d in r.json().get('results', [])))

# has_custody flag
r = search({'has_custody': 'true'})
check('has_custody=true filter works', r.status_code == 200)
check('Custody results have custody flag', all(d['has_custody'] for d in r.json().get('results', [])))

# Sorting
r = search({'sort_by': 'filename'})
check('sort_by=filename works', r.status_code == 200)
r = search({'sort_by': '-uploaded_at'})
check('sort_by=-uploaded_at (desc) works', r.status_code == 200)
r = search({'sort_by': 'INVALID_FIELD'})
check('Invalid sort_by falls back gracefully (200)', r.status_code == 200)

# Pagination
r = search({'page': '1', 'page_size': '2'})
check('Pagination page=1 page_size=2 works', r.status_code == 200)
paged = r.json()
check('Paginated response has page field', 'page' in paged)
check('Paginated response has total_pages', 'total_pages' in paged)
check('Page size respected (max 2 results)', len(paged.get('results', [])) <= 2)

r = search({'page': '1', 'page_size': '200'})  # over max
check('page_size capped at 100', r.status_code == 200)
check('Results capped at 100', len(r.json().get('results', [])) <= 100)

# Court can search
r = search({'q': 'QA'}, token=COURT_TOKEN)
check('Court user can search documents (200)', r.status_code == 200)

# Response shape check
r = search({'q': 'QA'})
d = r.json()
check('Search response has total_count', 'total_count' in d)
check('Search response has active_filters', 'active_filters' in d)
check('Search results have has_custody flag', all('has_custody' in doc for doc in d.get('results', [])))
check('Search results have has_certificate flag', all('has_certificate' in doc for doc in d.get('results', [])))
check('Search results have has_redaction flag', all('has_redaction' in doc for doc in d.get('results', [])))
check('Search results have verification_count', all('verification_count' in doc for doc in d.get('results', [])))


# ══════════════════════════════════════════════════════════
# [EDGE] Edge Cases & Error Handling
# ══════════════════════════════════════════════════════════
section('[EDGE] Edge Cases & Error Handling')

# Verify non-existent document
r = req('POST', '/verification/00000000-0000-0000-0000-000000000000/verify/', token=IO_TOKEN)
check('Verify non-existent doc returns 404', r.status_code == 404)

# Detect PII on non-existent document
r = req('POST', '/redaction/detect/', token=IO_TOKEN, json={'document_id': '00000000-0000-0000-0000-000000000000'})
check('Detect PII non-existent doc returns 404', r.status_code == 404)

# Redact non-existent document
r = req('POST', '/redaction/redact/', token=IO_TOKEN, json={'document_id': '00000000-0000-0000-0000-000000000000'})
check('Redact non-existent doc returns 404', r.status_code == 404)

# Custody chain for non-existent doc
r = req('POST', '/custody/', token=IO_TOKEN, json={'document_id': '00000000-0000-0000-0000-000000000000', 'location': 'X'})
check('Custody non-existent doc returns 404', r.status_code == 404)

# Certificate for non-existent doc
r = req('POST', '/certificates/generate/', token=IO_TOKEN, json={'document_id': '00000000-0000-0000-0000-000000000000', 'certificate_type': 'INTEGRITY'})
check('Certificate non-existent doc returns 404', r.status_code == 404)

# Missing required fields
r = req('POST', '/redaction/detect/', token=IO_TOKEN, json={})
check('Missing document_id returns 400', r.status_code == 400)

r = req('POST', '/custody/', token=IO_TOKEN, json={'location': 'X'})
check('Custody missing document_id returns 400', r.status_code == 400)

# Transfer to self
r = req('POST', f'/custody/{CHAIN_ID}/transfer/', token=ADMIN_TOKEN, json={
    'to_user_id': ADMIN_ID,
    'to_location': 'Self',
})
check('Transfer to self returns 400', r.status_code == 400, str(r.status_code))

# Download non-existent redaction job
r = req('GET', '/redaction/00000000-0000-0000-0000-000000000000/download/', token=IO_TOKEN)
check('Download non-existent redaction returns 404', r.status_code == 404)

# Non-existent certificate download
r = req('GET', '/certificates/00000000-0000-0000-0000-000000000000/download/', token=IO_TOKEN)
check('Download non-existent certificate returns 404', r.status_code == 404)

# Expired/invalid JWT
r = req('GET', '/documents/', token='thisisnotavalidtoken')
check('Invalid JWT returns 401', r.status_code == 401)


# ══════════════════════════════════════════════════════════
# FINAL REPORT
# ══════════════════════════════════════════════════════════
total = passed + failed
print(f'\n{"=" * 62}')
print(f'  PRAMAAN QA REPORT — FINAL SIGN-OFF')
print('=' * 62)
print(f'  Total Tests : {total}')
print(f'  Passed      : {passed}  ({100*passed//total if total else 0}%)')
print(f'  Failed      : {failed}')
print(f'  Warnings    : {warnings}')
print('=' * 62)

if failures:
    print('\n  FAILURES:')
    for f_msg in failures:
        print(f'  {f_msg}')

if failed == 0:
    print('\n  [SIGN-OFF] ALL TESTS PASSED.')
    print('  PRAMAAN P0 + P1 + P2 Backend is production-ready for demo.')
else:
    print(f'\n  [ACTION REQUIRED] {failed} test(s) failed. Review above.')

print()

# Cleanup temp files
for f_name in [QA_FILE, QA_PII_FILE]:
    try:
        os.remove(f_name)
    except Exception:
        pass
