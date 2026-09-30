"""
demo_p1.py — PRAMAAN P1 Demo Script (Chain of Custody + Certificate)
Run: python -X utf8 demo_p1.py

Demonstrates P1 flow:
  1.  Login as IO (Inspector Sharma)
  2.  Upload a new evidence document
  3.  Verify integrity -> VERIFIED
  4.  Register evidence into custody chain (IO holder)
  5.  Initiate transfer: IO -> CFSL Officer (inspector_sharma -> admin acting as CFSL)
  6.  Confirm transfer as receiver
  7.  View full custody history (chronological timeline)
  8.  Generate COURT_EXPORT PDF certificate
  9.  Download the PDF certificate
  10. View audit logs -> CUSTODY_TRANSFER + CERT_GENERATE entries
"""
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import os
import requests

BASE_URL  = 'http://127.0.0.1:8000/api/v1'
DEMO_FILE = 'demo_evidence.txt'


def sep(title=''):
    print('\n' + '=' * 62)
    if title:
        print(f'  {title}')
        print('=' * 62)


# ---------------------------------------------------------------------------
# STEP 0: Create evidence file
# ---------------------------------------------------------------------------
def create_evidence_file():
    sep('STEP 0 -- Creating demo evidence file')
    content = (
        "FORENSIC EVIDENCE REPORT\n"
        "==========================\n"
        "Case No      : CASE-2026-001\n"
        "Evidence ID  : EV-CFSL-2026-042\n"
        "Date         : 29-Sep-2026\n"
        "Station      : CFSL Mumbai\n"
        "Examiner     : Dr. A. Verma\n\n"
        "Findings     : Forensic examination of seized hard disk (500GB).\n"
        "               Found encrypted files containing financial records.\n"
        "               MD5, SHA-256 hashes verified. No signs of modification.\n\n"
        "Status       : Under Analysis\n"
        "Classification: CONFIDENTIAL\n"
    )
    with open(DEMO_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'  [OK] Created: {DEMO_FILE}')


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def login(username, password, role_label):
    resp = requests.post(f'{BASE_URL}/auth/login/', json={'username': username, 'password': password})
    if resp.status_code != 200:
        print(f'  [FAIL] Login failed for {username}: {resp.json()}')
        sys.exit(1)
    data = resp.json()
    print(f'  [OK] Logged in: {data["user"]["full_name"]} [{data["user"]["role"]}] as {role_label}')
    return data['access'], data['user']


# ---------------------------------------------------------------------------
# STEP 1: Login
# ---------------------------------------------------------------------------
def step_login():
    sep('STEP 1 -- Login as Investigating Officer')
    return login('inspector_sharma', 'IO@12345', 'IO')


# ---------------------------------------------------------------------------
# STEP 2: Upload evidence
# ---------------------------------------------------------------------------
def step_upload(token):
    sep('STEP 2 -- Upload Evidence Document')
    headers = {'Authorization': f'Bearer {token}'}
    with open(DEMO_FILE, 'rb') as f:
        resp = requests.post(
            f'{BASE_URL}/documents/upload/',
            headers=headers,
            files={'file': (DEMO_FILE, f, 'text/plain')},
            data={'case_id': 'CASE-2026-001', 'description': 'Forensic evidence report'}
        )
    data = resp.json()
    if resp.status_code != 201:
        print(f'  [FAIL] Upload failed: {data}')
        sys.exit(1)
    print(f'  [OK] Document uploaded!')
    print(f'       ID      : {data["id"]}')
    print(f'       SHA-256 : {data["sha256_hash"]}')
    print(f'       Status  : {data["status"]}')
    return data['id'], data['sha256_hash']


# ---------------------------------------------------------------------------
# STEP 3: Verify integrity
# ---------------------------------------------------------------------------
def step_verify(token, doc_id):
    sep('STEP 3 -- Verify Document Integrity')
    headers = {'Authorization': f'Bearer {token}'}
    resp = requests.post(f'{BASE_URL}/verification/{doc_id}/verify/', headers=headers)
    data = resp.json()
    verdict = data.get('verdict', '?')
    print(f'  [OK] Verdict : {verdict}')
    print(f'       {data["message"]}')
    return data['verification']['id']


# ---------------------------------------------------------------------------
# STEP 4: Register into Custody Chain
# ---------------------------------------------------------------------------
def step_register_custody(token, doc_id):
    sep('STEP 4 -- Register Evidence into Custody Chain')
    headers = {'Authorization': f'Bearer {token}'}
    resp = requests.post(f'{BASE_URL}/custody/', json={
        'document_id': doc_id,
        'location': 'Cyber Crime Unit, Mumbai'
    }, headers=headers)
    data = resp.json()
    if resp.status_code != 201:
        print(f'  [FAIL] {data}')
        sys.exit(1)
    chain_id = data['id']
    print(f'  [OK] Custody chain registered!')
    print(f'       Chain ID        : {chain_id}')
    print(f'       Current Holder  : {data["current_holder"]["full_name"]}')
    print(f'       Location        : {data["current_location"]}')
    print(f'       Status          : {data["status"]}')
    return chain_id


# ---------------------------------------------------------------------------
# STEP 5: Initiate Transfer IO -> Admin (acting as CFSL)
# ---------------------------------------------------------------------------
def step_initiate_transfer(token, chain_id, to_user_id):
    sep('STEP 5 -- Initiate Transfer: IO -> CFSL Lab (Mumbai)')
    headers = {'Authorization': f'Bearer {token}'}
    resp = requests.post(f'{BASE_URL}/custody/{chain_id}/transfer/', json={
        'to_user_id':      str(to_user_id),
        'to_location':     'CFSL Lab, Mumbai',
        'transfer_reason': 'Forwarding for advanced forensic analysis',
        'notes':           'Handle with care. Encrypted files inside.'
    }, headers=headers)
    data = resp.json()
    if resp.status_code != 201:
        print(f'  [FAIL] {data}')
        sys.exit(1)
    t_id = data['transfer']['id']
    print(f'  [OK] Transfer initiated!')
    print(f'       Transfer ID  : {t_id}')
    print(f'       To           : {data["transfer"]["to_user"]["full_name"]}')
    print(f'       To Location  : {data["transfer"]["to_location"]}')
    print(f'       Status       : {data["transfer"]["status"]}')
    print(f'       Hash Snapshot: {data["transfer"]["document_hash_at_transfer"][:20]}...')
    return t_id


# ---------------------------------------------------------------------------
# STEP 6: Confirm Transfer (login as receiver = admin/CFSL)
# ---------------------------------------------------------------------------
def step_confirm_transfer(t_id):
    sep('STEP 6 -- Confirm Transfer (CFSL Receiver Confirms Receipt)')
    # Login as Admin (acting as CFSL officer)
    cfsl_token, cfsl_user = login('admin', 'Admin@1234', 'CFSL Receiver')
    headers = {'Authorization': f'Bearer {cfsl_token}'}
    resp = requests.post(f'{BASE_URL}/custody/transfer/{t_id}/confirm/', json={
        'notes': 'Evidence received in sealed condition. Hash verified.'
    }, headers=headers)
    data = resp.json()
    if resp.status_code != 200:
        print(f'  [FAIL] {data}')
        sys.exit(1)
    print(f'  [OK] {data["message"]}')
    print(f'       Status       : {data["transfer"]["status"]}')
    print(f'       Confirmed At : {data["transfer"]["confirmed_at"]}')


# ---------------------------------------------------------------------------
# STEP 7: View full custody history
# ---------------------------------------------------------------------------
def step_custody_history(token, chain_id):
    sep('STEP 7 -- Full Chain of Custody History')
    headers = {'Authorization': f'Bearer {token}'}
    resp = requests.get(f'{BASE_URL}/custody/{chain_id}/history/', headers=headers)
    data = resp.json()
    print(f'  [OK] Document        : {data["document"]}')
    print(f'       Current Holder  : {data["current_holder"]}')
    print(f'       Current Status  : {data["current_status"]}')
    print(f'       Total Transfers : {data["transfer_count"]}')
    print()
    print('  Transfer Timeline:')
    for i, t in enumerate(data['history'], 1):
        frm  = t['from_user']['full_name'] if t.get('from_user') else '?'
        to   = t['to_user']['full_name']   if t.get('to_user')   else '?'
        loc  = t['to_location'] or '—'
        stat = t['status']
        date = t['initiated_at'][:10]
        print(f'  {i}. {frm:20} -> {to:20} | {loc:25} | {stat:10} | {date}')


# ---------------------------------------------------------------------------
# STEP 8: Generate PDF Certificate
# ---------------------------------------------------------------------------
def step_generate_certificate(token, doc_id):
    sep('STEP 8 -- Generate Court Export PDF Certificate')
    headers = {'Authorization': f'Bearer {token}'}
    resp = requests.post(f'{BASE_URL}/certificates/generate/', json={
        'document_id':      doc_id,
        'certificate_type': 'COURT_EXPORT'
    }, headers=headers)
    data = resp.json()
    if resp.status_code != 201:
        print(f'  [FAIL] {data}')
        sys.exit(1)
    cert = data['certificate']
    cert_id = cert['id']
    print(f'  [OK] {data["message"]}')
    print(f'       Certificate No  : {cert["certificate_number"]}')
    print(f'       Type            : {cert["certificate_type_display"]}')
    print(f'       PDF SHA-256     : {cert["sha256_of_pdf"][:24]}...')
    print(f'       Generated At    : {cert["generated_at"]}')
    return cert_id, cert['certificate_number']


# ---------------------------------------------------------------------------
# STEP 9: Download PDF Certificate
# ---------------------------------------------------------------------------
def step_download_certificate(token, cert_id, cert_number):
    sep('STEP 9 -- Download PDF Certificate')
    headers = {'Authorization': f'Bearer {token}'}
    resp = requests.get(f'{BASE_URL}/certificates/{cert_id}/download/', headers=headers, stream=True)
    if resp.status_code != 200:
        print(f'  [FAIL] HTTP {resp.status_code}')
        return
    filename = f'{cert_number}.pdf'
    with open(filename, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    size_kb = os.path.getsize(filename) / 1024
    print(f'  [OK] Certificate downloaded!')
    print(f'       File       : {filename}')
    print(f'       Size       : {size_kb:.1f} KB')
    print(f'       Header SHA : {resp.headers.get("X-PDF-SHA256", "N/A")[:24]}...')
    print(f'       [Open {filename} to view the PDF!]')


# ---------------------------------------------------------------------------
# STEP 10: View updated audit logs
# ---------------------------------------------------------------------------
def step_audit_logs(token):
    sep('STEP 10 -- Audit Logs (CUSTODY_TRANSFER + CERT_GENERATE entries)')
    headers = {'Authorization': f'Bearer {token}'}
    resp = requests.get(f'{BASE_URL}/audit/?limit=15', headers=headers)
    data = resp.json()
    print(f'  [OK] Total audit entries: {data["count"]}')
    print()
    for log in data['results']:
        user_name = log['user']['full_name'] if log.get('user') else 'System'
        sev  = log['severity']
        icon = {'INFO': '[INFO]', 'WARNING': '[WARN]', 'CRITICAL': '[CRIT]'}.get(sev, '[????]')
        print(f'  {icon} {log["action_display"]:28} | {user_name:26} | {log["result"]}')


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    sep('PRAMAAN -- SIH PS 26190 -- P1 Demo Flow')
    print('  Chain of Custody + Legal Certificate Export')
    print('  Stack: Django + DRF + ReportLab + SQLite + JWT')

    create_evidence_file()
    io_token, io_user = step_login()
    doc_id, sha256    = step_upload(io_token)
    ver_id            = step_verify(io_token, doc_id)
    chain_id          = step_register_custody(io_token, doc_id)

    # Get admin user ID for transfer target
    admin_resp = requests.post(f'{BASE_URL}/auth/login/',
                               json={'username': 'admin', 'password': 'Admin@1234'})
    admin_id = admin_resp.json()['user']['id']

    t_id              = step_initiate_transfer(io_token, chain_id, admin_id)
    step_confirm_transfer(t_id)
    step_custody_history(io_token, chain_id)

    # Re-login as IO for certificate
    io_token2, _ = login('inspector_sharma', 'IO@12345', 'IO (re-login)')
    cert_id, cert_number = step_generate_certificate(io_token2, doc_id)
    step_download_certificate(io_token2, cert_id, cert_number)
    step_audit_logs(io_token2)

    sep('[DONE] P1 Demo Complete!')
    print('  [OK] 6. Chain of Custody -- IO register + transfer + CFSL confirm')
    print('  [OK] 7. Legal/Evidence Certificate -- PDF with hash + timestamp + chain')
    print()
    print(f'  PDF Certificate saved to: {cert_number}.pdf')
    print('  Open it to see the full PRAMAAN certificate!')
    print()


if __name__ == '__main__':
    main()
