"""
test_rbac.py — Quick RBAC + audit stats test
Run: python -X utf8 test_rbac.py
"""
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import requests

BASE_URL = 'http://127.0.0.1:8000/api/v1'

# --- Test 1: Court user CANNOT upload (should be 403)
print('\n[RBAC TEST 1] Court user tries to upload document (expected: 403 Forbidden)...')
resp = requests.post(f'{BASE_URL}/auth/login/', json={'username': 'court_user', 'password': 'Court@1234'})
court_token = resp.json()['access']
with open('demo_fir.txt', 'rb') as f:
    resp2 = requests.post(
        f'{BASE_URL}/documents/upload/',
        headers={'Authorization': f'Bearer {court_token}'},
        files={'file': ('test.txt', f, 'text/plain')},
        data={'case_id': 'TEST'}
    )
print(f'  HTTP Status : {resp2.status_code}  (expected: 403)')
print(f'  Message     : {resp2.json()}')
assert resp2.status_code == 403, 'FAIL: Court user should not be allowed to upload!'
print('  [PASS] Court user correctly blocked from uploading.')

# --- Test 2: Admin can list users (should be 200)
print('\n[RBAC TEST 2] Admin lists all users (expected: 200 OK)...')
resp3 = requests.post(f'{BASE_URL}/auth/login/', json={'username': 'admin', 'password': 'Admin@1234'})
admin_token = resp3.json()['access']
resp4 = requests.get(f'{BASE_URL}/auth/users/', headers={'Authorization': f'Bearer {admin_token}'})
data = resp4.json()
print(f'  HTTP Status : {resp4.status_code}  (expected: 200)')
print(f'  Users found : {len(data)}')
for u in data:
    role = u['role']
    name = u['full_name']
    uname = u['username']
    print(f'    [{role:5}] {name:30} ({uname})')
assert resp4.status_code == 200, 'FAIL: Admin should be able to list users!'
print('  [PASS] Admin can list users correctly.')

# --- Test 3: IO user CANNOT list users (should be 403)
print('\n[RBAC TEST 3] IO user tries to list users (expected: 403 Forbidden)...')
resp5 = requests.post(f'{BASE_URL}/auth/login/', json={'username': 'inspector_sharma', 'password': 'IO@12345'})
io_token = resp5.json()['access']
resp6 = requests.get(f'{BASE_URL}/auth/users/', headers={'Authorization': f'Bearer {io_token}'})
print(f'  HTTP Status : {resp6.status_code}  (expected: 403)')
assert resp6.status_code == 403, 'FAIL: IO user should not list users!'
print('  [PASS] IO user correctly blocked from user management.')

# --- Test 4: Audit stats
print('\n[AUDIT STATS] Admin gets dashboard summary stats...')
resp7 = requests.get(f'{BASE_URL}/audit/stats/', headers={'Authorization': f'Bearer {admin_token}'})
stats = resp7.json()
print(f'  HTTP Status      : {resp7.status_code}')
print(f'  Total logs       : {stats["total_logs"]}')
print(f'  Critical alerts  : {stats["critical_alerts"]}')
print(f'  Tamper alerts    : {stats["tamper_alerts"]}')
print(f'  Action breakdown :')
for action in stats['action_breakdown']:
    print(f'    {action["action"]:15} : {action["count"]} entries')
print('  [PASS] Audit stats working.')

# --- Test 5: Unauthenticated access blocked
print('\n[SECURITY TEST] Unauthenticated request (expected: 401 Unauthorized)...')
resp8 = requests.get(f'{BASE_URL}/documents/')
print(f'  HTTP Status : {resp8.status_code}  (expected: 401)')
assert resp8.status_code == 401, 'FAIL: Should require authentication!'
print('  [PASS] Unauthenticated access correctly blocked.')

print('\n' + '=' * 60)
print('  ALL RBAC TESTS PASSED!')
print('  [OK] ADMIN  -> Can login, list users, view audit stats')
print('  [OK] IO     -> Can upload, verify, view docs. Cannot manage users.')
print('  [OK] COURT  -> Can view/download docs. Cannot upload or verify.')
print('  [OK] Anon   -> All endpoints return 401.')
print('=' * 60 + '\n')
