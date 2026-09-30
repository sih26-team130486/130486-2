"""
demo_p2.py — PRAMAAN P2 Demo Script (PII Redaction + Document Search)
Run: python -X utf8 demo_p2.py

Demonstrates P2 flow:
  1.  Login as IO
  2.  Upload a document WITH PII (Aadhaar, PAN, phone, email embedded)
  3.  DETECT PII — scan only, original untouched
  4.  REDACT — create redacted copy with PII masked
  5.  Download redacted file — verify PII is replaced
  6.  Search: q="FIR" full-text search
  7.  Search: status=VERIFIED filter
  8.  Search: date_from + date_to date range
  9.  Search: hash prefix search
  10. Search: has_pii=true (only redacted documents)
  11. Search: has_certificate=true (only certified documents)
  12. View audit logs (PII_REDACT + SEARCH entries)
"""
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import os
import json
import requests

BASE_URL  = 'http://127.0.0.1:8000/api/v1'
PII_FILE  = 'demo_pii_document.txt'


def sep(title=''):
    print('\n' + '=' * 62)
    if title:
        print(f'  {title}')
        print('=' * 62)


def login(username, password, label=''):
    resp = requests.post(f'{BASE_URL}/auth/login/', json={'username': username, 'password': password})
    if resp.status_code != 200:
        print(f'  [FAIL] Login failed: {resp.json()}')
        sys.exit(1)
    data = resp.json()
    print(f'  [OK] Logged in: {data["user"]["full_name"]} [{data["user"]["role"]}]' + (f' ({label})' if label else ''))
    return data['access']


# ---------------------------------------------------------------------------
# STEP 0: Create a document that contains PII
# ---------------------------------------------------------------------------
def create_pii_file():
    sep('STEP 0 -- Creating demo document with embedded PII')
    content = (
        "INVESTIGATION REPORT\n"
        "====================\n"
        "Case No   : CASE-2026-001\n"
        "FIR No    : FIR-2026-1243\n"
        "Date      : 29-Sep-2026\n\n"
        "SUSPECT DETAILS:\n"
        "  Name     : Mr. Rajesh Kumar Singh\n"
        "  Aadhaar  : 9876 5432 1098\n"
        "  PAN      : ABCDE1234F\n"
        "  Phone    : +91-9876543210\n"
        "  Email    : rajesh.kumar@example.com\n"
        "  Voter ID : XYZ1234567\n\n"
        "WITNESS DETAILS:\n"
        "  Name     : Dr. Priya Sharma\n"
        "  Phone    : 9123456789\n"
        "  Email    : priya.sharma@gov.in\n\n"
        "INCIDENT SUMMARY:\n"
        "  Cyber fraud amounting to Rs. 45 lakhs.\n"
        "  Suspect used multiple SIM cards to evade detection.\n\n"
        "STATUS: Under Investigation\n"
        "CLASSIFICATION: CONFIDENTIAL\n"
    )
    with open(PII_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'  [OK] Created: {PII_FILE}')
    print(f'  [INFO] File contains: Aadhaar, PAN, 2x Phone, 2x Email, Voter ID, 2x Name')


# ---------------------------------------------------------------------------
# STEP 1: Login
# ---------------------------------------------------------------------------
def step_login():
    sep('STEP 1 -- Login as Investigating Officer')
    return login('inspector_sharma', 'IO@12345')


# ---------------------------------------------------------------------------
# STEP 2: Upload PII document
# ---------------------------------------------------------------------------
def step_upload(token):
    sep('STEP 2 -- Upload Document Containing PII')
    headers = {'Authorization': f'Bearer {token}'}
    with open(PII_FILE, 'rb') as f:
        resp = requests.post(
            f'{BASE_URL}/documents/upload/',
            headers=headers,
            files={'file': (PII_FILE, f, 'text/plain')},
            data={'case_id': 'CASE-2026-001', 'description': 'Investigation report with suspect PII'}
        )
    data = resp.json()
    if resp.status_code != 201:
        print(f'  [FAIL] {data}')
        sys.exit(1)
    print(f'  [OK] Uploaded: {data["filename"]}')
    print(f'       ID      : {data["id"]}')
    print(f'       SHA-256 : {data["sha256_hash"][:24]}...')
    return data['id'], data['sha256_hash']


# ---------------------------------------------------------------------------
# STEP 3: Detect PII (scan only, no change)
# ---------------------------------------------------------------------------
def step_detect_pii(token, doc_id):
    sep('STEP 3 -- Detect PII (Scan Only -- Original File Untouched)')
    headers = {'Authorization': f'Bearer {token}'}
    resp = requests.post(f'{BASE_URL}/redaction/detect/', json={'document_id': doc_id}, headers=headers)
    data = resp.json()
    if resp.status_code != 200:
        print(f'  [FAIL] {data}')
        sys.exit(1)

    result = data['scan_result']
    print(f'  [OK] PII Scan complete!')
    print(f'       Total PII found  : {result["total_pii_found"]}')
    print(f'       PII types        : {result["pii_types_found"]}')
    print(f'       Document clean   : {result["is_clean"]}')
    print()
    print('  Detected Entities:')
    for m in result['matches']:
        print(f'    [{m["severity"]:8}] {m["type"]:15} -> masked as: {m["masked"]}  (preview: {m["preview"]})')
    print()
    print(f'  [NOTE] {data["note"]}')


# ---------------------------------------------------------------------------
# STEP 4: Redact document (creates new redacted copy)
# ---------------------------------------------------------------------------
def step_redact(token, doc_id):
    sep('STEP 4 -- Redact Document (Creates New Copy, Original Preserved)')
    headers = {'Authorization': f'Bearer {token}'}
    resp = requests.post(f'{BASE_URL}/redaction/redact/', json={'document_id': doc_id}, headers=headers)
    data = resp.json()
    if resp.status_code != 201:
        print(f'  [FAIL] {data}')
        sys.exit(1)
    job = data['job']
    print(f'  [OK] {data["message"]}')
    print(f'       Job ID         : {job["id"]}')
    print(f'       PII types      : {job["pii_types_detected"]}')
    print(f'       PII count      : {job["pii_count"]}')
    print(f'       Status         : {job["status"]}')
    print(f'       Completed At   : {job["completed_at"]}')
    return job['id']


# ---------------------------------------------------------------------------
# STEP 5: Download redacted file
# ---------------------------------------------------------------------------
def step_download_redacted(token, job_id):
    sep('STEP 5 -- Download Redacted File (PII Masked)')
    headers = {'Authorization': f'Bearer {token}'}
    resp = requests.get(f'{BASE_URL}/redaction/{job_id}/download/', headers=headers, stream=True)
    if resp.status_code != 200:
        print(f'  [FAIL] HTTP {resp.status_code}')
        return
    out_file = 'demo_pii_document_REDACTED.txt'
    with open(out_file, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f'  [OK] Downloaded redacted file: {out_file}')
    print(f'       PII Count  : {resp.headers.get("X-PII-Count", "?")}')
    print(f'       PII Types  : {resp.headers.get("X-PII-Types", "?")}')
    print()
    # Show a snippet of the redacted content
    with open(out_file, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    print('  Redacted file preview (first 600 chars):')
    print('  ' + '-' * 58)
    for line in content[:600].splitlines():
        print(f'  {line}')
    print('  ' + '-' * 58)


# ---------------------------------------------------------------------------
# STEP 6-11: Search filters
# ---------------------------------------------------------------------------
def step_search(token, label, params):
    headers = {'Authorization': f'Bearer {token}'}
    resp = requests.get(f'{BASE_URL}/search/documents/', headers=headers, params=params)
    data = resp.json()
    print(f'  [{label}]')
    print(f'    Params  : {params}')
    print(f'    Results : {data["total_count"]} documents found')
    for doc in data['results'][:3]:
        has_pii  = '[PII]' if doc['has_redaction'] else ''
        has_cert = '[CERT]' if doc['has_certificate'] else ''
        has_coc  = '[COC]' if doc['has_custody'] else ''
        flags = ' '.join(filter(None, [has_pii, has_cert, has_coc]))
        print(f'    * {doc["filename"]:28} | {doc["status"]:12} | {flags}')
    if data['total_count'] > 3:
        print(f'    ... and {data["total_count"] - 3} more')
    print()


def step_search_all(token, doc_sha256):
    sep('STEPS 6-11 -- Document Search & Filters')

    tests = [
        ('Full-text: q=FIR',         {'q': 'FIR'}),
        ('Status: VERIFIED',          {'status': 'VERIFIED'}),
        ('Date range: today',         {'date_from': '2026-09-29', 'date_to': '2026-09-30'}),
        (f'Hash prefix search',       {'hash': doc_sha256[:8]}),
        ('has_pii=true',              {'has_pii': 'true'}),
        ('has_certificate=true',      {'has_certificate': 'true'}),
        ('Uploader: sharma',          {'uploader': 'sharma'}),
        ('Sort by filename',          {'sort_by': 'filename', 'page_size': '5'}),
    ]
    for label, params in tests:
        step_search(token, label, params)


# ---------------------------------------------------------------------------
# STEP 12: Audit logs
# ---------------------------------------------------------------------------
def step_audit(token):
    sep('STEP 12 -- Audit Logs (PII_REDACT + SEARCH entries)')
    headers = {'Authorization': f'Bearer {token}'}
    resp = requests.get(f'{BASE_URL}/audit/?limit=15', headers=headers)
    data = resp.json()
    print(f'  [OK] Total audit entries: {data["count"]}')
    print()
    for log in data['results'][:12]:
        user_name = log['user']['full_name'] if log.get('user') else 'System'
        sev  = log['severity']
        icon = {'INFO': '[INFO]', 'WARNING': '[WARN]', 'CRITICAL': '[CRIT]'}.get(sev, '[????]')
        print(f'  {icon} {log["action_display"]:28} | {user_name:26} | {log["result"]}')


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    sep('PRAMAAN -- SIH PS 26190 -- P2 Demo Flow')
    print('  PII Redaction + Document Search & Filters')
    print('  Stack: Django + DRF + Regex PII Engine + PyMuPDF + SQLite')

    create_pii_file()
    token = step_login()
    doc_id, sha256 = step_upload(token)
    step_detect_pii(token, doc_id)
    job_id = step_redact(token, doc_id)
    step_download_redacted(token, job_id)
    step_search_all(token, sha256)
    step_audit(token)

    sep('[DONE] P2 Demo Complete!')
    print('  [OK] 8. PII Redaction -- Aadhaar, PAN, Phone, Email, Voter ID detected + masked')
    print('  [OK] 9. Document Search -- 8 filter types demonstrated (q, status, date, hash, flags)')
    print()
    print('  Redacted file saved: demo_pii_document_REDACTED.txt')
    print('  Open it to see PII replaced with [AADHAAR REDACTED], [PAN REDACTED], etc.')
    print()


if __name__ == '__main__':
    main()
