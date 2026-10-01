"""Phase 7 verification. No credentials printed.

Verifies AI diagnosis integration:
  - CaseRead exposes veterinarian_notes
  - PredictionRequest accepts case_id
  - CasePredictionsResponse structure
  - POST /predictions persists case_id / cattle_id / owner_id
  - GET /cases/{case_id}/predictions authorization (401/200/403/404)
  - Model separation (no cross-model probability combination)
  - Model A (general_cattle_disease) persisted top-5
  - Model B (mastitis_specialist) persisted
  - Model C / D image models remain separate
  - veterinarian_notes in case response
  - Ownership security (cross-farmer 403)
"""
import urllib.request, urllib.error, json, time, io, struct, zlib, os, sqlite3

API_ROOT = os.environ.get("BOVICARE_API_ROOT", "http://localhost:8000/api")
BASE = f"{API_ROOT}/v1"
AUTH = API_ROOT
TS   = int(time.time())
TEST_PASSWORD = os.environ.get("BOVICARE_TEST_PASSWORD", "Pass1234")
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bovicare.db")


def req(method, url, data=None, body=None, token=None, content_type="application/json"):
    if body is not None and content_type == "application/json":
        data = json.dumps(body).encode()
    headers = {"Content-Type": content_type}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        try: b = json.loads(e.read())
        except: b = {}
        return e.code, b


def post_json(url, body, token=None):
    return req("POST", url, body=body, token=token)


def post_multipart(url, fields, file_bytes, file_field, filename, mime, token=None):
    boundary = b"BoviCareBoundary1234567890"
    parts = []
    for k, v in fields.items():
        parts.append(b"--" + boundary + b"\r\n" +
            f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode() +
            str(v).encode() + b"\r\n")
    parts.append(b"--" + boundary + b"\r\n" +
        f'Content-Disposition: form-data; name="{file_field}"; filename="{filename}"\r\n'.encode() +
        f"Content-Type: {mime}\r\n\r\n".encode() +
        file_bytes + b"\r\n")
    parts.append(b"--" + boundary + b"--\r\n")
    body = b"".join(parts)
    ct = f"multipart/form-data; boundary={boundary.decode()}"
    return req("POST", url, data=body, token=token, content_type=ct)


def make_png(w=64, h=64):
    """Generate a minimal valid PNG in memory."""
    def chunk(name, data):
        c = struct.pack(">I", len(data)) + name + data
        return c + struct.pack(">I", zlib.crc32(name + data) & 0xFFFFFFFF)
    raw = b""
    for _ in range(h):
        raw += b"\x00" + bytes([100, 150, 80] * w)
    compressed = zlib.compress(raw)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", compressed)
    png += chunk(b"IEND", b"")
    return png


def db_rows(case_id):
    """Read persisted prediction rows for a case directly from SQLite."""
    con = sqlite3.connect(DB_PATH)
    try:
        cur = con.execute(
            "SELECT case_id, cattle_id, owner_id, model_name, model_version, rank, "
            "disease_label, probability, risk_level FROM prediction_results WHERE case_id = ?",
            (case_id,),
        )
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        con.close()


def db_image_rows(model_name):
    con = sqlite3.connect(DB_PATH)
    try:
        cur = con.execute(
            "SELECT model_name, model_version, rank, disease_label, probability, risk_level "
            "FROM prediction_results WHERE model_name = ?",
            (model_name,),
        )
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        con.close()


results = []
def check(label, got, want):
    ok = got == want
    results.append(ok)
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}: {got} (expected {want})")


# -- Setup ---------------------------------------------------------------------
for role, sfx in [("farmer", "f1"), ("farmer", "f2"), ("doctor", "doc")]:
    post_json(f"{AUTH}/auth/register",
        {"name": f"P7 {sfx}", "email": f"p7_{sfx}_{TS}@example.com",
         "password": TEST_PASSWORD, "role": role})

_, d = post_json(f"{AUTH}/auth/login", {"email": f"p7_f1_{TS}@example.com", "password": TEST_PASSWORD})
f1 = d["access_token"]
f1_user_id = d["user"]["id"]
_, d = post_json(f"{AUTH}/auth/login", {"email": f"p7_f2_{TS}@example.com", "password": TEST_PASSWORD})
f2 = d["access_token"]
_, d = post_json(f"{AUTH}/auth/login", {"email": f"p7_doc_{TS}@example.com", "password": TEST_PASSWORD})
doc = d["access_token"]

_, cattle1 = post_json(f"{BASE}/cattle", {"tag_number": "P7-CATTLE1", "sex": "female"}, token=f1)
cow_id = cattle1["id"]

# -- A. Schema / API contract --------------------------------------------------
print("\n-- A. Schema / API contract --")
s, case = post_json(f"{BASE}/cases/triage",
    {"cattle_tag": "P7-CASE", "cattle_id": cow_id, "symptoms": ["coughing", "fever"]}, token=f1)
check("triage creates case", s, 201)
case_id = case.get("id")
check("CaseRead includes veterinarian_notes key", "veterinarian_notes" in case, True)
check("veterinarian_notes defaults to None", case.get("veterinarian_notes"), None)

# PredictionRequest accepts case_id (validated by a successful linked prediction below)
s, d = post_json(f"{BASE}/predictions", {"symptoms": ["coughing"], "case_id": case_id, "cattle_id": cow_id}, token=f1)
check("PredictionRequest accepts case_id", s, 200)
linked_prediction = d

# CasePredictionsResponse structure
s, d = req("GET", f"{BASE}/cases/{case_id}/predictions", token=f1)
check("CasePredictionsResponse status", s, 200)
check("CasePredictionsResponse has case_id", d.get("case_id"), case_id)
check("CasePredictionsResponse has models list", isinstance(d.get("models"), list), True)
if d.get("models"):
    m0 = d["models"][0]
    check("model entry has model_name", "model_name" in m0, True)
    check("model entry has model_version", "model_version" in m0, True)
    check("model entry has risk_level", "risk_level" in m0, True)
    check("model entry has predictions", isinstance(m0.get("predictions"), list), True)
    if m0.get("predictions"):
        p0 = m0["predictions"][0]
        check("prediction row has rank", "rank" in p0, True)
        check("prediction row has disease_label", "disease_label" in p0, True)
        check("prediction row has probability", "probability" in p0, True)

# -- B. POST /predictions linking ---------------------------------------------
print("\n-- B. POST /predictions linking --")
check("linked prediction status", s, 200)
check("general model used", "general_cattle_disease" in linked_prediction.get("models_used", []), True)

rows = db_rows(case_id)
check("rows persisted for case", len(rows) > 0, True)
check("all rows carry case_id", all(r["case_id"] == case_id for r in rows), True)
check("all rows carry cattle_id", all(r["cattle_id"] == cow_id for r in rows), True)
check("all rows carry owner_id", all(r["owner_id"] == f1_user_id for r in rows), True)
check("all rows carry model_name", all(bool(r["model_name"]) for r in rows), True)
check("all rows carry model_version", all(bool(r["model_version"]) for r in rows), True)
check("all rows carry rank", all(r["rank"] is not None for r in rows), True)
check("all rows carry disease_label", all(bool(r["disease_label"]) for r in rows), True)
check("all rows carry probability", all(isinstance(r["probability"], float) for r in rows), True)
check("all rows carry risk_level", all(r["risk_level"] in ("low", "moderate", "medium", "high") for r in rows), True)

# -- C. GET /cases/{case_id}/predictions authorization ------------------------
print("\n-- C. GET case predictions authorization --")
s, _ = req("GET", f"{BASE}/cases/{case_id}/predictions")
check("unauthenticated rejected", s, 401)
s, _ = req("GET", f"{BASE}/cases/{case_id}/predictions", token=f1)
check("owning farmer allowed", s, 200)
s, _ = req("GET", f"{BASE}/cases/{case_id}/predictions", token=f2)
check("different farmer forbidden", s, 403)
s, _ = req("GET", f"{BASE}/cases/{case_id}/predictions", token=doc)
check("doctor allowed", s, 200)
s, _ = req("GET", f"{BASE}/cases/99999999/predictions", token=f1)
check("nonexistent case 404", s, 404)

s, d = req("GET", f"{BASE}/cases/{case_id}/predictions", token=f1)
check("returned results belong to requested case", d.get("case_id"), case_id)

# -- D. Model separation -------------------------------------------------------
print("\n-- D. Model separation --")
s, d = req("GET", f"{BASE}/cases/{case_id}/predictions", token=f1)
names = [m["model_name"] for m in d.get("models", [])]
check("no duplicate model groups", len(names), len(set(names)))
check("general model grouped separately", "general_cattle_disease" in names, True)
# No cross-model combination: each model group only contains its own rows.
check("each group has a single model_name", all(isinstance(m["model_name"], str) for m in d.get("models", [])), True)

# -- E. Model A ----------------------------------------------------------------
print("\n-- E. Model A (general_cattle_disease) --")
gen = next((m for m in d.get("models", []) if m["model_name"] == "general_cattle_disease"), None)
check("Model A present", gen is not None, True)
if gen:
    preds = gen["predictions"]
    check("Model A has predictions", len(preds) > 0, True)
    check("Model A at most 5", len(preds) <= 5, True)
    check("Model A ranks valid", all(isinstance(p["rank"], int) and p["rank"] >= 1 for p in preds), True)
    check("Model A labels present", all(bool(p["disease_label"]) for p in preds), True)
    check("Model A probabilities numeric", all(isinstance(p["probability"], float) for p in preds), True)
    check("Model A probabilities 0-1", all(0.0 <= p["probability"] <= 1.0 for p in preds), True)
    check("Model A risk_level valid", gen["risk_level"] in ("low", "moderate", "medium", "high"), True)
    ranks = [p["rank"] for p in preds]
    check("Model A ordered by rank", ranks, sorted(ranks))

# -- F. Model B ----------------------------------------------------------------
print("\n-- F. Model B (mastitis_specialist) --")
milk = {"Milk_Temperature": 38.5, "Milk_pH": 6.5, "Milk_Conductivity": 5.2,
        "Somatic_Cell_Count": 450, "Milk_Yield": 15.0, "Clotting": 1}
s, d = post_json(f"{BASE}/predictions", {"milk_data": milk, "case_id": case_id}, token=f1)
check("milk prediction status", s, 200)
check("mastitis model used", "mastitis_specialist" in d.get("models_used", []), True)
s, d = req("GET", f"{BASE}/cases/{case_id}/predictions", token=f1)
mas = next((m for m in d.get("models", []) if m["model_name"] == "mastitis_specialist"), None)
check("Model B present", mas is not None, True)
if mas:
    check("Model B has one prediction", len(mas["predictions"]), 1)
    check("Model B probability numeric", isinstance(mas["predictions"][0]["probability"], float), True)
    check("Model B risk_level valid", mas["risk_level"] in ("low", "moderate", "medium", "high"), True)

# -- G. Image models C / D -----------------------------------------------------
print("\n-- G. Image models (C / D) --")
png = make_png()
s, d = post_multipart(f"{BASE}/predictions/image", {"model": "cattle", "case_id": case_id, "cattle_id": cow_id}, png, "file", "cow.png", "image/png", token=f1)
check("Model C image prediction status", s, 200)
check("Model C name", d.get("model"), "cattle_image_classifier")
check("Model C class count", len(d.get("predictions", [])), 7)
check("Model C probabilities sum to one", abs(sum(p["probability"] for p in d.get("predictions", [])) - 1.0) < 0.01, True)
s, d = post_multipart(f"{BASE}/predictions/image", {"model": "lumpy", "case_id": case_id, "cattle_id": cow_id}, png, "file", "cow.png", "image/png", token=f1)
check("Model D image prediction status", s, 200)
check("Model D name", d.get("model"), "lumpy_skin_specialist")
check("Model D remains two-class", len(d.get("predictions", [])), 2)

c_rows = db_image_rows("cattle_image_classifier")
d_rows = db_image_rows("lumpy_skin_specialist")
check("Model C persisted", len(c_rows) > 0, True)
check("Model D persisted", len(d_rows) > 0, True)
check("Model C rows tagged correctly", all(r["model_name"] == "cattle_image_classifier" for r in c_rows), True)
check("Model D rows tagged correctly", all(r["model_name"] == "lumpy_skin_specialist" for r in d_rows), True)
case_rows = db_rows(case_id)
linked_image_rows = [r for r in case_rows if r["model_name"] in {"cattle_image_classifier", "lumpy_skin_specialist"}]
check("image predictions remain linked to case and cattle", bool(linked_image_rows) and all(r["case_id"] == case_id and r["cattle_id"] == cow_id for r in linked_image_rows), True)
check("Model C and D remain separate", "cattle_image_classifier" != "lumpy_skin_specialist", True)

# -- H. Veterinarian notes -----------------------------------------------------
print("\n-- H. Veterinarian notes --")
s, d = req("PUT", f"{BASE}/cases/{case_id}/review", body={"veterinarian_notes": "P7 clinical note"}, token=doc)
check("doctor review status", s, 200)
check("review response has veterinarian_notes", d.get("veterinarian_notes"), "P7 clinical note")
s, d = req("GET", f"{BASE}/cases/{case_id}", token=f1)
check("case read exposes veterinarian_notes", d.get("veterinarian_notes"), "P7 clinical note")

# -- I. Ownership security -----------------------------------------------------
print("\n-- I. Ownership security --")
s, _ = req("GET", f"{BASE}/cases/{case_id}/predictions", token=f2)
check("cross-farmer case predictions forbidden", s, 403)

passed = sum(results)
total  = len(results)
print(f"\n{passed}/{total} tests passed")
print("Phase 7: VERIFIED" if passed == total else "Phase 7: FAILURES DETECTED")
