"""Phase 4 verification — cattle management + diagnosis linking. No credentials printed."""
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
            body = resp.read()
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        try: body = json.loads(e.read())
        except: body = {}
        return e.code, body

results = []

def check(label, got, want):
    ok = got == want
    results.append(ok)
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}: {got} (expected {want})")

# ── Setup: register two farmers and one doctor ──────────────────────────────
for role, suffix in [("farmer", "f1"), ("farmer", "f2"), ("doctor", "doc")]:
    req("POST", f"{AUTH}/auth/register",
        {"name": f"User {suffix}", "email": f"p4_{suffix}_{TS}@example.com",
         "password": "Pass1234", "role": role})

_, d = req("POST", f"{AUTH}/auth/login", {"email": f"p4_f1_{TS}@example.com", "password": "Pass1234"})
f1_tok = d["access_token"]
_, d = req("POST", f"{AUTH}/auth/login", {"email": f"p4_f2_{TS}@example.com", "password": "Pass1234"})
f2_tok = d["access_token"]
_, d = req("POST", f"{AUTH}/auth/login", {"email": f"p4_doc_{TS}@example.com", "password": "Pass1234"})
doc_tok = d["access_token"]

print("\n-- Cattle CRUD --")

# Unauthenticated request rejected
s, _ = req("GET", f"{BASE}/cattle")
check("unauthenticated cattle list rejected", s, 401)

# Farmer creates cattle
s, d = req("POST", f"{BASE}/cattle", {"tag_number": "COW-001", "sex": "female", "breed": "Holstein"}, token=f1_tok)
check("farmer creates cattle", s, 201)
cow1_id = d.get("id")

# Farmer lists own cattle
s, d = req("GET", f"{BASE}/cattle", token=f1_tok)
check("farmer lists own cattle", s, 200)
check("farmer sees own cattle in list", any(c["id"] == cow1_id for c in d), True)

# Farmer gets own cattle
s, _ = req("GET", f"{BASE}/cattle/{cow1_id}", token=f1_tok)
check("farmer gets own cattle", s, 200)

# Farmer updates own cattle
s, d = req("PUT", f"{BASE}/cattle/{cow1_id}", {"name": "Bessie", "weight_kg": 550.0}, token=f1_tok)
check("farmer updates own cattle", s, 200)
check("update reflected in response", d.get("name") == "Bessie", True)

# Doctor cannot create cattle
s, _ = req("POST", f"{BASE}/cattle", {"tag_number": "DOC-001", "sex": "male"}, token=doc_tok)
check("doctor cannot create cattle", s, 403)

# Doctor cannot update cattle
s, _ = req("PUT", f"{BASE}/cattle/{cow1_id}", {"name": "Hacked"}, token=doc_tok)
check("doctor cannot update cattle", s, 403)

# Doctor cannot delete cattle
s, _ = req("DELETE", f"{BASE}/cattle/{cow1_id}", token=doc_tok)
check("doctor cannot delete cattle", s, 403)

# Farmer 2 cannot access farmer 1's cattle
s, _ = req("GET", f"{BASE}/cattle/{cow1_id}", token=f2_tok)
check("cross-farmer cattle access rejected", s, 403)

# Farmer 2 cannot update farmer 1's cattle
s, _ = req("PUT", f"{BASE}/cattle/{cow1_id}", {"name": "Stolen"}, token=f2_tok)
check("cross-farmer cattle update rejected", s, 403)

# Farmer 2 cannot delete farmer 1's cattle
s, _ = req("DELETE", f"{BASE}/cattle/{cow1_id}", token=f2_tok)
check("cross-farmer cattle delete rejected", s, 403)

print("\n-- Diagnosis + cattle linking --")

# Farmer creates case linked to own cattle
s, d = req("POST", f"{BASE}/cases/triage",
           {"cattle_tag": "COW-001", "cattle_id": cow1_id, "symptoms": ["cough"]}, token=f1_tok)
check("farmer creates case linked to own cattle", s, 201)
check("case has cattle_id set", d.get("cattle_id") == cow1_id, True)
case_id = d.get("id")

# Farmer 2 cannot create case using farmer 1's cattle
s, _ = req("POST", f"{BASE}/cases/triage",
           {"cattle_tag": "COW-001", "cattle_id": cow1_id, "symptoms": ["cough"]}, token=f2_tok)
check("farmer cannot use another farmer's cattle in triage", s, 403)

# Triage without cattle_id still works (backward compat)
s, d = req("POST", f"{BASE}/cases/triage",
           {"cattle_tag": "MANUAL-TAG", "symptoms": ["lethargy"]}, token=f1_tok)
check("triage without cattle_id still works", s, 201)
check("case without cattle_id has null cattle_id", d.get("cattle_id") is None, True)

print("\n-- Phase 3 regression --")

# Farmer list cases
s, _ = req("GET", f"{BASE}/cases", token=f1_tok)
check("farmer list own cases", s, 200)

# Doctor list cases
s, _ = req("GET", f"{BASE}/cases", token=doc_tok)
check("doctor list all cases", s, 200)

# Doctor review
s, _ = req("PUT", f"{BASE}/cases/{case_id}/review",
           {"veterinarian_notes": "Looks fine."}, token=doc_tok)
check("doctor review still works", s, 200)

# Farmer cannot review
s, _ = req("PUT", f"{BASE}/cases/{case_id}/review",
           {"veterinarian_notes": "Farmer hack."}, token=f1_tok)
check("farmer review still rejected", s, 403)

# Farmer deletes own cattle
s, _ = req("DELETE", f"{BASE}/cattle/{cow1_id}", token=f1_tok)
check("farmer deletes own cattle", s, 204)

# Confirm deleted
s, _ = req("GET", f"{BASE}/cattle/{cow1_id}", token=f1_tok)
check("deleted cattle returns 404", s, 404)

# ── Summary ──────────────────────────────────────────────────────────────────
passed = sum(results)
total  = len(results)
print(f"\n{passed}/{total} tests passed")
print("Phase 4: VERIFIED" if passed == total else "Phase 4: FAILURES DETECTED")
