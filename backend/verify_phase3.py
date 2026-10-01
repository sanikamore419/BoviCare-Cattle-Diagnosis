"""Phase 3 verification — prints PASS/FAIL per test, no credentials."""
import os
import urllib.request, urllib.error, json, time

API_ROOT = os.environ.get("BOVICARE_API_ROOT", "http://localhost:8000/api")
BASE = f"{API_ROOT}/v1"
AUTH = API_ROOT
TS   = int(time.time())

def req(method, url, body=None, token=None):
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())

results = []

def check(label, got, want):
    ok = got == want
    results.append(ok)
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}: {got} (expected {want})")

# --- Registration ---
s, _ = req("POST", f"{AUTH}/auth/register",
           {"name": "V Farmer", "email": f"vf_{TS}@example.com",
            "password": "Pass1234", "role": "farmer"})
check("farmer registration", s, 201)

s, _ = req("POST", f"{AUTH}/auth/register",
           {"name": "V Farmer", "email": f"vf_{TS}@example.com",
            "password": "Pass1234", "role": "farmer"})
check("duplicate registration rejected", s, 409)

s, _ = req("POST", f"{AUTH}/auth/register",
           {"name": "V Doctor", "email": f"vd_{TS}@example.com",
            "password": "Pass1234", "role": "doctor"})
check("doctor registration", s, 201)

# --- Login ---
s, d = req("POST", f"{AUTH}/auth/login",
           {"email": f"vf_{TS}@example.com", "password": "Pass1234"})
check("farmer login", s, 200)
farmer_tok = d.get("access_token", "")

s, _ = req("POST", f"{AUTH}/auth/login",
           {"email": f"vf_{TS}@example.com", "password": "wrongpass"})
check("invalid login rejected", s, 401)

s, d = req("POST", f"{AUTH}/auth/login",
           {"email": f"vd_{TS}@example.com", "password": "Pass1234"})
check("doctor login", s, 200)
doctor_tok = d.get("access_token", "")

# --- /me ---
s, d = req("GET", f"{AUTH}/auth/me", token=farmer_tok)
check("/me authenticated", s, 200)

s, _ = req("GET", f"{AUTH}/auth/me")
check("/me unauthenticated rejected", s, 401)

# --- Triage ---
s, _ = req("POST", f"{BASE}/cases/triage",
           {"cattle_tag": "T1", "symptoms": ["cough"]})
check("unauthenticated triage rejected", s, 401)

s, _ = req("POST", f"{BASE}/cases/triage",
           {"cattle_tag": "T1", "symptoms": ["cough"]}, token=doctor_tok)
check("doctor triage rejected (farmer-only)", s, 403)

s, d = req("POST", f"{BASE}/cases/triage",
           {"cattle_tag": "T1", "symptoms": ["cough"]}, token=farmer_tok)
check("farmer triage succeeded", s, 201)
case_id = d.get("id")

# --- Case retrieval ---
s, _ = req("GET", f"{BASE}/cases", token=farmer_tok)
check("farmer list own cases", s, 200)

s, _ = req("GET", f"{BASE}/cases", token=doctor_tok)
check("doctor list all cases", s, 200)

s, _ = req("GET", f"{BASE}/cases/{case_id}", token=farmer_tok)
check("farmer get own case", s, 200)

# --- Cross-ownership protection ---
s, _ = req("POST", f"{AUTH}/auth/register",
           {"name": "Other Farmer", "email": f"vof_{TS}@example.com",
            "password": "Pass1234", "role": "farmer"})
s, d2 = req("POST", f"{AUTH}/auth/login",
            {"email": f"vof_{TS}@example.com", "password": "Pass1234"})
other_tok = d2.get("access_token", "")
s, _ = req("GET", f"{BASE}/cases/{case_id}", token=other_tok)
check("cross-farmer access rejected", s, 403)

# --- Review authorization ---
s, _ = req("PUT", f"{BASE}/cases/{case_id}/review",
           {"veterinarian_notes": "Looks fine."}, token=farmer_tok)
check("farmer review rejected (doctor-only)", s, 403)

s, _ = req("PUT", f"{BASE}/cases/{case_id}/review",
           {"veterinarian_notes": "Looks fine."}, token=doctor_tok)
check("doctor review succeeded", s, 200)

# --- Summary ---
passed = sum(results)
total  = len(results)
print(f"\n{passed}/{total} tests passed")
print("Phase 3: VERIFIED" if passed == total else "Phase 3: FAILURES DETECTED")
