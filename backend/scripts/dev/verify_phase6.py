"""Phase 6 verification. No credentials printed."""
import urllib.request, urllib.error, urllib.parse, json, time, io, struct, zlib, os

API_ROOT = os.environ.get("BOVICARE_API_ROOT", "http://localhost:8000/api")
BASE = f"{API_ROOT}/v1"
AUTH = API_ROOT
TS   = int(time.time())
TEST_PASSWORD = os.environ.get("BOVICARE_TEST_PASSWORD", "Pass1234")

def req(method, url, body=None, token=None, content_type="application/json"):
    data = json.dumps(body).encode() if body and content_type == "application/json" else body
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

def multipart(url, fields, file_bytes, file_field, filename, mime, token=None):
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

results = []
def check(label, got, want):
    ok = got == want
    results.append(ok)
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}: {got} (expected {want})")

# Setup
for role, sfx in [("farmer","f1"),("farmer","f2"),("doctor","doc")]:
    post_json(f"{AUTH}/auth/register",
        {"name": f"P6 {sfx}", "email": f"p6_{sfx}_{TS}@example.com",
         "password": TEST_PASSWORD, "role": role})

_, d = post_json(f"{AUTH}/auth/login", {"email": f"p6_f1_{TS}@example.com", "password": TEST_PASSWORD})
f1 = d["access_token"]
_, d = post_json(f"{AUTH}/auth/login", {"email": f"p6_f2_{TS}@example.com", "password": TEST_PASSWORD})
f2 = d["access_token"]
_, d = post_json(f"{AUTH}/auth/login", {"email": f"p6_doc_{TS}@example.com", "password": TEST_PASSWORD})
doc = d["access_token"]

_, cattle1 = post_json(f"{BASE}/cattle", {"tag_number": "P6-CATTLE1", "sex": "female"}, token=f1)
cow_id = cattle1["id"]
_, cattle2 = post_json(f"{BASE}/cattle", {"tag_number": "P6-CATTLE2", "sex": "male"}, token=f2)
cow2_id = cattle2["id"]

png = make_png()

print("\n-- Image security --")
s, _ = post_multipart(f"{BASE}/predictions/image", {}, png, "file", "test.png", "image/png")
check("unauthenticated image upload rejected", s, 401)

s, _ = post_multipart(f"{BASE}/predictions/image", {"cattle_id": cow_id}, png, "file", "test.png", "image/png", token=f2)
check("cross-farmer cattle image rejected", s, 403)

s, _ = post_multipart(f"{BASE}/predictions/image", {}, b"not an image at all", "file", "bad.txt", "text/plain", token=f1)
check("unsupported file type rejected", s, 415)

print("\n-- Image prediction: cattle model --")
s, d = post_multipart(f"{BASE}/predictions/image", {"model": "cattle"}, png, "file", "cow.png", "image/png", token=f1)
check("cattle image prediction status", s, 200)
check("model name correct", d.get("model") == "cattle_image_classifier", True)
check("Model C version identified", d.get("model_version") == "bovicare-cattle-image-efficientnet-b0-v1", True)
check("predictions present", len(d.get("predictions", [])) > 0, True)
expected_classes = {"HEALTHY", "LSD", "RINGWORM", "FMD", "IBK", "PEDICULOSIS", "DERMATOPHILOSIS"}
check("Model C returns exact trained classes", {p.get("label") for p in d.get("predictions", [])} == expected_classes, True)
check("top_label present", bool(d.get("top_label")), True)
check("top_probability 0-1", 0.0 <= d.get("top_probability", -1) <= 1.0, True)
check("risk_level valid", d.get("risk_level") in ("low","moderate","high"), True)
check("disclaimer present", "disclaimer" in d, True)
preds = d.get("predictions", [])
check("predictions have rank", all("rank" in p for p in preds), True)
check("predictions have label", all("label" in p for p in preds), True)
check("predictions have probability", all("probability" in p for p in preds), True)
check("probabilities are bounded", all(0.0 <= p["probability"] <= 1.0 for p in preds), True)
check("probabilities sum ~1", abs(sum(p["probability"] for p in preds) - 1.0) < 0.01, True)

s, _ = post_multipart(f"{BASE}/predictions/image", {"model": "cattle"}, b"not an image", "file", "bad.png", "image/png", token=f1)
check("corrupt image rejected", s, 415)

print("\n-- Image prediction: lumpy skin model --")
s, d = post_multipart(f"{BASE}/predictions/image", {"model": "lumpy"}, png, "file", "cow.png", "image/png", token=f1)
check("lumpy skin prediction status", s, 200)
check("lumpy model name correct", d.get("model") == "lumpy_skin_specialist", True)
check("lumpy predictions present", len(d.get("predictions", [])) == 2, True)

print("\n-- Image prediction: cattle-linked --")
s, d = post_multipart(f"{BASE}/predictions/image", {"model": "cattle", "cattle_id": cow_id}, png, "file", "cow.png", "image/png", token=f1)
check("cattle-linked image prediction", s, 200)
check("cattle_id in response", d.get("cattle_id") == cow_id, True)

print("\n-- Doctor can run image prediction --")
s, d = post_multipart(f"{BASE}/predictions/image", {"model": "cattle"}, png, "file", "cow.png", "image/png", token=doc)
check("doctor image prediction allowed", s, 200)

print("\n-- Phase 5 regression: symptom prediction --")
s, d = post_json(f"{BASE}/predictions", {"symptoms": ["coughing", "fever"]}, token=f1)
check("symptom prediction still works", s, 200)
check("general model still runs", "general_cattle_disease" in d.get("models_used", []), True)

print("\n-- Phase 5 regression: mastitis prediction --")
milk = {"Milk_Temperature": 38.5, "Milk_pH": 6.5, "Milk_Conductivity": 5.2,
        "Somatic_Cell_Count": 450, "Milk_Yield": 15.0, "Clotting": 1}
s, d = post_json(f"{BASE}/predictions", {"milk_data": milk}, token=f1)
check("mastitis prediction still works", s, 200)
check("mastitis model still runs", "mastitis_specialist" in d.get("models_used", []), True)

print("\n-- Phase 3/4 regression --")
s, _ = req("GET", f"{AUTH}/auth/me")
check("/me unauthenticated rejected", s, 401)
s, _ = req("GET", f"{AUTH}/auth/me", token=f1)
check("/me authenticated", s, 200)
s, d = post_json(f"{BASE}/cases/triage", {"cattle_tag": "T1", "symptoms": ["cough"]}, token=f1)
check("farmer triage", s, 201)
case_id = d.get("id")
s, _ = req("PUT", f"{BASE}/cases/{case_id}/review", body={"veterinarian_notes": "OK"}, token=f1)
check("farmer review rejected", s, 403)
s, _ = req("PUT", f"{BASE}/cases/{case_id}/review", body={"veterinarian_notes": "OK"}, token=doc)
check("doctor review works", s, 200)
s, _ = req("GET", f"{BASE}/cattle/{cow2_id}", token=f1)
check("cross-farmer cattle access rejected", s, 403)

passed = sum(results)
total  = len(results)
print(f"\n{passed}/{total} tests passed")
print("Phase 6: VERIFIED" if passed == total else "Phase 6: FAILURES DETECTED")
