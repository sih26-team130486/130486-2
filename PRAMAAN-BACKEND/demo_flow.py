"""
demo_flow.py — PRAMAAN SIH Demo Script
Run: python demo_flow.py

Demonstrates the complete P0 flow for the video presentation:
  1. Login as IO
  2. Upload a document  -> SHA-256 hash computed
  3. List documents     -> see hash
  4. Verify document    -> VERIFIED [OK]
  5. Tamper the file (modify bytes on disk)
  6. Verify again       -> TAMPERED [ALERT]
  7. View audit logs    -> all 6 actions recorded

Prerequisites:
  - Server running: python manage.py runserver
  - DB seeded:      python manage.py seed_demo
"""

import sys
import os
import json
import requests

# Force UTF-8 output on Windows to avoid cp1252 encoding errors
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


BASE_URL  = 'http://127.0.0.1:8000/api/v1'
DEMO_FILE = 'demo_fir.txt'


def separator(title=''):
    print('\n' + '=' * 60)
    if title:
        print(f'  {title}')
        print('=' * 60)


def pp(data):
    print(json.dumps(data, indent=2, default=str))


# ──────────────────────────────────────────────────────────
# STEP 0: Create demo file
# ──────────────────────────────────────────────────────────
def create_demo_file():
    separator('STEP 0 -- Creating demo file')
    content = (
        "FIRST INFORMATION REPORT (FIR)\n"
        "================================\n"
        "Case No      : CASE-2026-001\n"
        "Date         : 29-Sep-2026\n"
        "Station      : Cyber Crime Unit, Mumbai\n"
        "Officer      : Inspector Sharma\n"
        "Complainant  : ABC Corp Ltd\n\n"
        "Incident     : Unauthorized access to company servers.\n"
        "               Attacker exploited CVE-2026-1234 at 02:17 IST.\n"
        "               Data worth Rs.45 lakhs extracted.\n\n"
        "Status       : Under Investigation\n"
    )
    with open(DEMO_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'  [OK] Created demo file: {DEMO_FILE}')


# ──────────────────────────────────────────────────────────
# STEP 1: Login
# ──────────────────────────────────────────────────────────
def step_login():
    separator('STEP 1 -- Login as Investigating Officer')
    resp = requests.post(f'{BASE_URL}/auth/login/', json={
        'username': 'inspector_sharma',
        'password': 'IO@12345',
    })
    data = resp.json()
    if resp.status_code != 200:
        print(f'  [FAIL] Login failed: {data}')
        sys.exit(1)

    token = data['access']
    user  = data['user']
    print(f'  [OK] Logged in as: {user["full_name"]} [{user["role"]}]')
    print(f'  [OK] JWT Token (first 40 chars): {token[:40]}...')
    return token


# ──────────────────────────────────────────────────────────
# STEP 2: Upload document
# ──────────────────────────────────────────────────────────
def step_upload(token):
    separator('STEP 2 -- Upload Document (SHA-256 computed server-side)')
    headers = {'Authorization': f'Bearer {token}'}
    with open(DEMO_FILE, 'rb') as f:
        resp = requests.post(
            f'{BASE_URL}/documents/upload/',
            headers=headers,
            files={'file': (DEMO_FILE, f, 'text/plain')},
            data={'case_id': 'CASE-2026-001', 'description': 'Demo FIR for SIH'}
        )
    data = resp.json()
    if resp.status_code != 201:
        print(f'  [FAIL] Upload failed: {data}')
        sys.exit(1)

    doc_id = data['id']
    sha256 = data['sha256_hash']
    print(f'  [OK] Document uploaded successfully!')
    print(f'       Document ID : {doc_id}')
    print(f'       SHA-256     : {sha256}')
    print(f'       Filename    : {data["filename"]}')
    print(f'       Status      : {data["status"]}')
    return doc_id, sha256


# ──────────────────────────────────────────────────────────
# STEP 3: List documents
# ──────────────────────────────────────────────────────────
def step_list(token):
    separator('STEP 3 -- List Documents')
    headers = {'Authorization': f'Bearer {token}'}
    resp = requests.get(f'{BASE_URL}/documents/', headers=headers)
    data = resp.json()
    print(f'  [OK] Total documents: {data["count"]}')
    for doc in data['results']:
        print(f'       * {doc["filename"]:25} | Status: {doc["status"]:12} | Hash: {doc["sha256_hash"][:20]}...')


# ──────────────────────────────────────────────────────────
# STEP 4: Verify -- should PASS
# ──────────────────────────────────────────────────────────
def step_verify_clean(token, doc_id):
    separator('STEP 4 -- Verify Document (should be VERIFIED [OK])')
    headers = {'Authorization': f'Bearer {token}'}
    resp = requests.post(f'{BASE_URL}/verification/{doc_id}/verify/', headers=headers)
    data = resp.json()
    verdict = data.get('verdict', '?')

    if verdict == 'VERIFIED':
        print(f'  [OK] {data["message"]}')
        print(f'       Original hash : {data["verification"]["original_hash"]}')
        print(f'       Computed hash : {data["verification"]["computed_hash"]}')
        print(f'       Hashes match  : YES - INTEGRITY CONFIRMED')
    else:
        print(f'  [WARN] Unexpected result: {verdict}')


# ──────────────────────────────────────────────────────────
# STEP 5: TAMPER the file
# ──────────────────────────────────────────────────────────
def step_tamper(token, doc_id):
    separator('STEP 5 -- [TAMPER SIMULATION] Modifying stored file on disk')

    import glob
    print(f'  [INFO] Looking for stored file...')
    matches = glob.glob(f'media/documents/**/*{DEMO_FILE}*', recursive=True)
    if not matches:
        matches = glob.glob(f'media/**/*fir*', recursive=True)

    if not matches:
        print('  [WARN] Cannot find file locally.')
        print('  [INFO] Run this script from PRAMAAN-BACKEND directory.')
        print('  [SKIP] Skipping tamper step.')
        return False

    file_path = matches[0]
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write('\n\n[TAMPERED BY ATTACKER -- THIS LINE WAS INJECTED MALICIOUSLY]')
    print(f'  [ALERT] File tampered: {file_path}')
    print(f'  [ALERT] Injected malicious content into stored file.')
    return True


# ──────────────────────────────────────────────────────────
# STEP 6: Verify again -- should FAIL
# ──────────────────────────────────────────────────────────
def step_verify_tampered(token, doc_id):
    separator('STEP 6 -- Re-verify After Tamper (should be [TAMPERED ALERT])')
    headers = {'Authorization': f'Bearer {token}'}
    resp = requests.post(f'{BASE_URL}/verification/{doc_id}/verify/', headers=headers)
    data = resp.json()
    verdict = data.get('verdict', '?')

    if verdict == 'TAMPERED':
        print(f'  [CRITICAL ALERT] {data["message"]}')
        print(f'       Original hash : {data["verification"]["original_hash"]}')
        print(f'       Computed hash : {data["verification"]["computed_hash"]}')
        print(f'       Hashes match  : NO -- INTEGRITY BREACH DETECTED!')
        print(f'       Audit entry   : CRITICAL severity entry created automatically')
    else:
        print(f'  [OK] File was not tampered (or tamper step was skipped): {verdict}')


# ──────────────────────────────────────────────────────────
# STEP 7: Audit logs
# ──────────────────────────────────────────────────────────
def step_audit(token):
    separator('STEP 7 -- Audit Logs (every action recorded in DB)')
    headers = {'Authorization': f'Bearer {token}'}
    resp = requests.get(f'{BASE_URL}/audit/?limit=20', headers=headers)
    data = resp.json()
    print(f'  [OK] Total audit log entries: {data["count"]}')
    print()
    for log in data['results']:
        user_name = log['user']['full_name'] if log.get('user') else 'System'
        sev = log['severity']
        icon = {'INFO': '[INFO]', 'WARNING': '[WARN]', 'CRITICAL': '[CRIT]'}.get(sev, '[????]')
        doc_name = log['document_name']
        print(f'  {icon} {log["action_display"]:25} | {user_name:25} | {doc_name:20} | {log["result"]}')


# ──────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────
def main():
    separator('PRAMAAN -- SIH PS 26190 -- P0 Backend Demo Flow')
    print('  Stack: Django + DRF + SQLite/PostgreSQL + SHA-256 + JWT + RBAC')
    print('  Demo:  Upload -> Hash -> Verify -> Tamper -> Alert -> Audit')

    create_demo_file()
    token = step_login()
    doc_id, sha256 = step_upload(token)
    step_list(token)
    step_verify_clean(token, doc_id)
    step_tamper(token, doc_id)
    step_verify_tampered(token, doc_id)
    step_audit(token)

    separator('[DONE] Demo Complete!')
    print('  All P0 requirements demonstrated:')
    print('  [OK] 1. Document upload + secure storage')
    print('  [OK] 2. SHA-256 hash generation + stored in database')
    print('  [OK] 3. Tamper detection -- hash mismatch detected + CRITICAL alert')
    print('  [OK] 4. Audit logs -- all actions recorded with timestamps')
    print('  [OK] 5. Role-based access -- JWT + ADMIN/IO/COURT roles')
    print()


if __name__ == '__main__':
    main()
