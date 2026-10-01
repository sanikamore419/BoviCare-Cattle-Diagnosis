"""Phase 8 verification. No credentials or model artifacts are printed."""
import json
import os
import re
import struct
import time
import urllib.error
import urllib.request
import zlib
import base64

API_ROOT = os.environ.get("BOVICARE_API_ROOT", "http://localhost:8000/api")
BASE = f"{API_ROOT}/v1"
AUTH = API_ROOT
TS = int(time.time())
TEST_PASSWORD = os.environ.get("BOVICARE_TEST_PASSWORD", "Pass1234")


def req(method, url, body=None, token=None, data=None, content_type="application/json"):
    if body is not None:
        data = json.dumps(body).encode()
    headers = {"Content-Type": content_type}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request) as response:
            raw = response.read()
            return response.status, json.loads(raw) if content_type == "application/json" and raw else raw
    except urllib.error.HTTPError as error:
        try:
            payload = json.loads(error.read())
        except Exception:
            payload = {}
        return error.code, payload


def multipart(url, fields, token=None):
    boundary = b"BoviCarePhase8Boundary"
    parts = []
    for key, value in fields.items():
        parts.append(b"--" + boundary + b"\r\n" + f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode() + str(value).encode() + b"\r\n")
    def chunk(name, payload):
        value = struct.pack(">I", len(payload)) + name + payload
        return value + struct.pack(">I", zlib.crc32(name + payload) & 0xFFFFFFFF)
    raw = b"\x00" + bytes([100, 150, 80] * 8)
    image = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 8, 1, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")
    parts.append(b"--" + boundary + b"\r\n" + b'Content-Disposition: form-data; name="file"; filename="cow.png"\r\n' + b"Content-Type: image/png\r\n\r\n" + image + b"\r\n")
    body = b"".join(parts) + b"--" + boundary + b"--\r\n"
    return req("POST", url, token=token, data=body, content_type=f"multipart/form-data; boundary={boundary.decode()}")


def pdf_text(pdf_bytes):
    text = pdf_bytes.decode("latin-1", errors="ignore")
    chunks = []
    for encoded in re.findall(rb"stream\s*(.*?)\s*endstream", pdf_bytes, re.DOTALL):
        try:
            chunks.append(zlib.decompress(encoded).decode("latin-1", errors="ignore"))
        except zlib.error:
            try:
                chunks.append(zlib.decompress(base64.a85decode(encoded, adobe=True)).decode("latin-1", errors="ignore"))
            except (ValueError, zlib.error):
                chunks.append(encoded.decode("latin-1", errors="ignore"))
    return text + "\n" + "\n".join(chunks)


results = []


def check(label, condition):
    ok = bool(condition)
    results.append(ok)
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}")


# Setup two farmers and one doctor.
for role, name in (("farmer", "owner"), ("farmer", "other"), ("doctor", "doctor")):
    req("POST", f"{AUTH}/auth/register", {"name": f"P8 {name}", "email": f"p8_{name}_{TS}@example.com", "password": TEST_PASSWORD, "role": role})

tokens = {}
for name in ("owner", "other", "doctor"):
    status, data = req("POST", f"{AUTH}/auth/login", {"email": f"p8_{name}_{TS}@example.com", "password": TEST_PASSWORD})
    check(f"{name} login", status == 200)
    tokens[name] = data.get("access_token", "")
owner_id = data.get("user", {}).get("id") if name == "doctor" else None
status, owner_data = req("POST", f"{AUTH}/auth/login", {"email": f"p8_owner_{TS}@example.com", "password": TEST_PASSWORD})
owner_id = owner_data.get("user", {}).get("id")

status, cattle = req("POST", f"{BASE}/cattle", {"tag_number": f"P8-COW-{TS}", "sex": "female", "breed": "Holstein"}, token=tokens["owner"])
check("owner creates cattle", status == 201)
cattle_id = cattle.get("id")
status, case = req("POST", f"{BASE}/cases/triage", {"cattle_tag": f"P8-COW-{TS}", "cattle_id": cattle_id, "breed": "Holstein", "age_years": 5, "symptoms": ["coughing", "fever"]}, token=tokens["owner"])
check("owner creates case", status == 201)
case_id = case.get("id")

print("\n-- Review security and persistence --")
review_body = {"veterinarian_notes": "Phase 8 clinical review note.", "review_status": "reviewed"}
status, _ = req("PUT", f"{BASE}/cases/{case_id}/review", review_body)
check("unauthenticated review update rejected", status == 401)
status, _ = req("PUT", f"{BASE}/cases/{case_id}/review", review_body, token=tokens["owner"])
check("farmer review update rejected", status == 403)
status, reviewed = req("PUT", f"{BASE}/cases/{case_id}/review", review_body, token=tokens["doctor"])
check("doctor review update succeeds", status == 200)
check("veterinarian notes persist", reviewed.get("veterinarian_notes") == review_body["veterinarian_notes"])
check("review status persists", reviewed.get("status") == "reviewed")

print("\n-- Prediction access and report --")
milk = {"Milk_Temperature": 38.5, "Milk_pH": 6.5, "Milk_Conductivity": 5.2, "Somatic_Cell_Count": 450, "Milk_Yield": 15.0, "Clotting": 1}
status, prediction = req("POST", f"{BASE}/predictions", {"case_id": case_id, "cattle_id": cattle_id, "symptoms": ["coughing", "fever"], "milk_data": milk}, token=tokens["owner"])
check("case-linked predictions succeed", status == 200)
check("general and mastitis stay separate", set(prediction.get("models_used", [])) == {"general_cattle_disease", "mastitis_specialist"})
status, _ = multipart(f"{BASE}/predictions/image", {"model": "cattle", "case_id": case_id, "cattle_id": cattle_id}, token=tokens["owner"])
check("case-linked cattle image prediction succeeds", status == 200)
status, _ = multipart(f"{BASE}/predictions/image", {"model": "lumpy", "case_id": case_id, "cattle_id": cattle_id}, token=tokens["owner"])
check("case-linked lumpy image prediction succeeds", status == 200)
status, case_predictions = req("GET", f"{BASE}/cases/{case_id}/predictions", token=tokens["owner"])
check("owner prediction access remains intact", status == 200)
check("all four model groups are available", {m["model_name"] for m in case_predictions.get("models", [])} == {"general_cattle_disease", "mastitis_specialist", "cattle_image_classifier", "lumpy_skin_specialist"})
status, _ = req("GET", f"{BASE}/cases/{case_id}/predictions", token=tokens["other"])
check("other farmer prediction access remains forbidden", status == 403)

status, report = req("GET", f"{BASE}/cases/{case_id}/report", token=tokens["doctor"], content_type="application/pdf")
check("doctor report download succeeds", status == 200)
check("report is a PDF", isinstance(report, bytes) and report.startswith(b"%PDF"))
report_text = pdf_text(report if isinstance(report, bytes) else b"")
for expected in ("BoviCare AI", f"Case ID: {case_id}", "Holstein", "coughing", "Phase 8 clinical review note.", "Review status: reviewed", "Model A", "Model B", "Model C", "Model D", "Disclaimer"):
    check(f"report contains {expected}", expected in report_text)

passed = sum(results)
total = len(results)
print(f"\n{passed}/{total} tests passed")
print("Phase 8: VERIFIED" if passed == total else "Phase 8: FAILURES DETECTED")
