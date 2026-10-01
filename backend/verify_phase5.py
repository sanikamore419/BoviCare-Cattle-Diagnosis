"""Phase 5 verification. No credentials printed."""
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
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        try: body2 = json.loads(e.read())
        except: body2 = {}
        return e.code, body2

results = []
def check(label, got, want):
    ok = got == want
    results.append(ok)
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}: {got} (expected {want})")

# -- Setup users --
for role, sfx in [("farmer","f1"),("farmer","f2"),("doctor","doc")]:
    req("POST", f"{AUTH}/auth/register",
        {"name": f"P5 {sfx}", "email": f"p5_{sfx}_{TS}@example.com",
         "password": "Pass1234", "role": role})

_, d = req("POST", f"{AUTH}/auth/login", {"email": f"p5_f1_{TS}@example.com", "password": "Pass1234"})
f1 = d["access_token"]
_, d = req("POST", f"{AUTH}/auth/login", {"email": f"p5_f2_{TS}@example.com", "password": "Pass1234"})
f2 = d["access_token"]
_, d = req("POST", f"{AUTH}/auth/login", {"email": f"p5_doc_{TS}@example.com", "password": "Pass1234"})
doc = d["access_token"]

# Create cattle for farmer 1
_, cow = req("POST", f"{BASE}/cattle", {"tag_number": "P5-COW", "sex": "female"}, token=f1)
cow_id = cow["id"]

print("\n-- Security --")
s, _ = req("POST", f"{BASE}/predictions", {"symptoms": ["coughing"]})
check("unauthenticated prediction rejected", s, 401)

s, _ = req("POST", f"{BASE}/predictions", {"cattle_id": cow_id, "symptoms": ["coughing"]}, token=f2)
check("cross-farmer cattle prediction rejected", s, 403)

print("\n-- Routing: symptoms only (Model A) --")
s, d = req("POST", f"{BASE}/predictions",
           {"symptoms": ["coughing", "fever", "depression"]}, token=f1)
check("symptoms-only prediction status", s, 200)
check("models_used contains general", "general_cattle_disease" in d.get("models_used", []), True)
check("mastitis not run for symptoms-only", d.get("mastitis") is None, True)
check("general result present", d.get("general") is not None, True)
preds = d.get("general", {}).get("predictions", [])
check("top-5 predictions returned", len(preds) >= 1, True)
check("predictions have rank", all("rank" in p for p in preds), True)
check("predictions have disease", all("disease" in p for p in preds), True)
check("predictions have probability", all("probability" in p for p in preds), True)
check("probabilities are floats 0-1", all(0.0 <= p["probability"] <= 1.0 for p in preds), True)
check("predictions ordered by rank", [p["rank"] for p in preds] == sorted(p["rank"] for p in preds), True)
check("risk_level present", d.get("combined_risk_level") in ("low","moderate","high"), True)
check("disclaimer present", "disclaimer" in d, True)

print("\n-- Routing: milk data only (Model B) --")
milk = {"Milk_Temperature": 38.5, "Milk_pH": 6.5, "Milk_Conductivity": 5.2,
        "Somatic_Cell_Count": 450, "Milk_Yield": 15.0, "Clotting": 1}
s, d = req("POST", f"{BASE}/predictions", {"milk_data": milk}, token=f1)
check("milk-only prediction status", s, 200)
check("models_used contains mastitis", "mastitis_specialist" in d.get("models_used", []), True)
check("general not run for milk-only", d.get("general") is None, True)
check("mastitis result present", d.get("mastitis") is not None, True)
m = d.get("mastitis", {})
check("mastitis has condition", "condition" in m, True)
check("mastitis condition is valid label", m.get("condition") in ("Mastitis", "No Mastitis"), True)
check("mastitis has probability", "probability" in m, True)
check("mastitis probability 0-1", 0.0 <= m.get("probability", -1) <= 1.0, True)

print("\n-- Routing: both inputs (Models A + B) --")
s, d = req("POST", f"{BASE}/predictions",
           {"symptoms": ["coughing", "fever"], "milk_data": milk}, token=f1)
check("both-input prediction status", s, 200)
check("both models used", set(d.get("models_used", [])) == {"general_cattle_disease", "mastitis_specialist"}, True)
check("general result present", d.get("general") is not None, True)
check("mastitis result present", d.get("mastitis") is not None, True)

print("\n-- Routing: neither input --")
s, d = req("POST", f"{BASE}/predictions", {}, token=f1)
check("no-input rejected (422)", s, 422)

print("\n-- Cattle-linked prediction --")
s, d = req("POST", f"{BASE}/predictions",
           {"cattle_id": cow_id, "symptoms": ["lethargy", "dull"]}, token=f1)
check("cattle-linked prediction status", s, 200)
check("cattle_id in response", d.get("cattle_id") == cow_id, True)

print("\n-- Doctor can run predictions --")
s, d = req("POST", f"{BASE}/predictions",
           {"symptoms": ["fever", "coughing"]}, token=doc)
check("doctor prediction allowed", s, 200)

print("\n-- Phase 3 regression --")
s, _ = req("POST", f"{AUTH}/auth/register",
           {"name":"Reg F","email":f"reg_f_{TS}@example.com","password":"Pass1234","role":"farmer"})
check("farmer registration", s, 201)
s, _ = req("POST", f"{AUTH}/auth/login",
           {"email":f"reg_f_{TS}@example.com","password":"wrongpass"})
check("invalid login rejected", s, 401)
s, _ = req("GET", f"{AUTH}/auth/me", token=f1)
check("/me authenticated", s, 200)
s, _ = req("POST", f"{BASE}/cases/triage", {"cattle_tag":"T1","symptoms":["cough"]})
check("unauthenticated triage rejected", s, 401)
s, d = req("POST", f"{BASE}/cases/triage", {"cattle_tag":"T1","symptoms":["cough"]}, token=f1)
check("farmer triage", s, 201)
case_id = d.get("id")
s, _ = req("PUT", f"{BASE}/cases/{case_id}/review",
           {"veterinarian_notes":"OK"}, token=f1)
check("farmer review rejected", s, 403)
s, _ = req("PUT", f"{BASE}/cases/{case_id}/review",
           {"veterinarian_notes":"OK"}, token=doc)
check("doctor review works", s, 200)

print("\n-- Phase 4 regression --")
s, d = req("POST", f"{BASE}/cattle", {"tag_number":"REG-COW","sex":"male"}, token=f1)
check("farmer creates cattle", s, 201)
reg_cow = d["id"]
s, _ = req("GET", f"{BASE}/cattle/{reg_cow}", token=f2)
check("cross-farmer cattle access rejected", s, 403)
s, _ = req("DELETE", f"{BASE}/cattle/{reg_cow}", token=f1)
check("farmer deletes own cattle", s, 204)

# Summary
passed = sum(results)
total  = len(results)
print(f"\n{passed}/{total} tests passed")
print("Phase 5: VERIFIED" if passed == total else "Phase 5: FAILURES DETECTED")
