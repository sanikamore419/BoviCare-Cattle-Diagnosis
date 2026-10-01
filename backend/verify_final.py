"""Concise end-to-end verification for the final BoviCare integration."""
import json
import os
import struct
import time
import urllib.error
import urllib.request
import zlib
import re
import base64

API_ROOT = os.environ.get("BOVICARE_API_ROOT", "http://localhost:8000/api")
BASE = f"{API_ROOT}/v1"
AUTH = API_ROOT
TS = int(time.time())
PASSWORD = os.environ.get("BOVICARE_TEST_PASSWORD", "Pass1234")


def request(method, url, body=None, token=None, data=None, content_type="application/json"):
    if body is not None:
        data = json.dumps(body).encode()
    headers = {"Content-Type": content_type}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=headers, method=method)) as response:
            raw = response.read()
            return response.status, json.loads(raw) if response.headers.get_content_type() == "application/json" and raw else raw
    except urllib.error.HTTPError as error:
        try:
            return error.code, json.loads(error.read())
        except Exception:
            return error.code, b""


def png():
    def chunk(name, payload):
        return struct.pack(">I", len(payload)) + name + payload + struct.pack(">I", zlib.crc32(name + payload) & 0xffffffff)
    raw = b"\x00" + bytes([100, 150, 80]) * 8
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 8, 1, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def upload(url, fields, payload, token):
    boundary = b"BoviCareFinalBoundary"
    parts = []
    for key, value in fields.items():
        parts.append(b"--" + boundary + b"\r\n" + f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode() + str(value).encode() + b"\r\n")
    parts.append(b'--' + boundary + b'\r\nContent-Disposition: form-data; name="file"; filename="final.png"\r\nContent-Type: image/png\r\n\r\n' + payload + b'\r\n--' + boundary + b'--\r\n')
    return request("POST", url, token=token, data=b"".join(parts), content_type=f"multipart/form-data; boundary={boundary.decode()}")


def pdf_text(pdf_bytes):
    text = pdf_bytes.decode("latin-1", errors="ignore")
    streams = []
    for encoded in re.findall(rb"stream\s*(.*?)\s*endstream", pdf_bytes, re.DOTALL):
        try:
            streams.append(zlib.decompress(encoded).decode("latin-1", errors="ignore"))
        except zlib.error:
            try:
                streams.append(zlib.decompress(base64.a85decode(encoded, adobe=True)).decode("latin-1", errors="ignore"))
            except (ValueError, zlib.error):
                streams.append(encoded.decode("latin-1", errors="ignore"))
    return text + "\n" + "\n".join(streams)


results = []
def check(label, condition):
    passed = bool(condition)
    results.append(passed)
    print(f"  [{'PASS' if passed else 'FAIL'}] {label}")


print("-- Authentication and ownership --")
tokens = {}
for role, name in (("farmer", "owner"), ("farmer", "other"), ("doctor", "doctor")):
    request("POST", f"{AUTH}/auth/register", {"name": f"Final {name}", "email": f"final_{name}_{TS}@example.com", "password": PASSWORD, "role": role})
    status, data = request("POST", f"{AUTH}/auth/login", {"email": f"final_{name}_{TS}@example.com", "password": PASSWORD})
    check(f"{name} login", status == 200)
    tokens[name] = data.get("access_token", "")
status, _ = request("GET", f"{AUTH}/auth/me", token=tokens["owner"])
check("authenticated /me", status == 200)
status, _ = request("GET", f"{AUTH}/auth/me")
check("unauthenticated /me rejected", status == 401)

status, cattle = request("POST", f"{BASE}/cattle", {"tag_number": f"FINAL-COW-{TS}", "sex": "female", "breed": "Holstein"}, tokens["owner"])
check("cattle creation", status == 201)
cattle_id = cattle.get("id")
status, case = request("POST", f"{BASE}/cases/triage", {"cattle_tag": f"FINAL-COW-{TS}", "cattle_id": cattle_id, "symptoms": ["difficulty breathing"], "temperature_c": 40.6}, tokens["owner"])
check("high-risk case creation", status == 201 and case.get("risk_level") == "high")
case_id = case.get("id")
status, _ = request("GET", f"{BASE}/cases/{case_id}", token=tokens["other"])
check("cross-farmer case blocked", status == 403)

print("\n-- Predictions and image --")
milk = {"Milk_Temperature": 38.5, "Milk_pH": 6.5, "Milk_Conductivity": 5.2, "Somatic_Cell_Count": 450, "Milk_Yield": 15.0, "Clotting": 1}
status, prediction = request("POST", f"{BASE}/predictions", {"case_id": case_id, "symptoms": ["difficulty breathing"], "milk_data": milk}, tokens["owner"])
check("Models A and B prediction", status == 200 and set(prediction.get("models_used", [])) == {"general_cattle_disease", "mastitis_specialist"})
status, _ = request("POST", f"{BASE}/predictions", {"case_id": case_id, "cattle_id": cattle_id + 999999, "symptoms": ["coughing"]}, tokens["owner"])
check("invalid cattle reference rejected", status == 404)
status, image_prediction = upload(f"{BASE}/predictions/image", {"case_id": case_id, "cattle_id": cattle_id, "model": "cattle"}, png(), tokens["owner"])
check("Model C image prediction", status == 200 and image_prediction.get("model") == "cattle_image_classifier")
status, image_prediction = upload(f"{BASE}/predictions/image", {"case_id": case_id, "model": "lumpy"}, png(), tokens["owner"])
check("Model D image prediction", status == 200 and image_prediction.get("model") == "lumpy_skin_specialist")
status, persisted = request("GET", f"{BASE}/cases/{case_id}/predictions", token=tokens["owner"])
model_names = {model["model_name"] for model in persisted.get("models", [])}
check("all four model results persisted separately", status == 200 and model_names == {"general_cattle_disease", "mastitis_specialist", "cattle_image_classifier", "lumpy_skin_specialist"})
status, image_bytes = request("GET", f"{BASE}/cases/{case_id}/image", token=tokens["owner"], content_type="image/png")
check("owner can access persisted image", status == 200 and image_bytes.startswith(b"\x89PNG"))
status, _ = request("GET", f"{BASE}/cases/{case_id}/image", token=tokens["other"])
check("other farmer image blocked", status == 403)

print("\n-- Veterinary workflow and report --")
status, notifications = request("GET", f"{BASE}/cases/{case_id}/notifications", token=tokens["doctor"])
check("doctor sees high-risk notification", status == 200 and len(notifications) >= 1)
status, reviewed = request("PUT", f"{BASE}/cases/{case_id}/review", {"veterinarian_notes": "Final integration review.", "review_status": "reviewed"}, tokens["doctor"])
check("doctor review succeeds", status == 200 and reviewed.get("status") == "reviewed")
status, _ = request("PUT", f"{BASE}/cases/{case_id}/review", {"veterinarian_notes": "Unauthorized", "review_status": "reviewed"}, tokens["owner"])
check("farmer review blocked", status == 403)
status, report = request("GET", f"{BASE}/cases/{case_id}/report", token=tokens["doctor"], content_type="application/pdf")
report_text = pdf_text(report) if isinstance(report, bytes) else ""
check("doctor PDF download", status == 200 and report.startswith(b"%PDF"))
for expected in ("Model A", "Model B", "Model C", "Model D", "Final integration review", "High-risk notifications", "Disclaimer"):
    check(f"PDF contains {expected}", expected in report_text)
status, farmer_english = request("GET", f"{BASE}/cases/{case_id}/report?language=en", token=tokens["owner"], content_type="application/pdf")
check("farmer English PDF download", status == 200 and farmer_english.startswith(b"%PDF"))
status, farmer_marathi = request("GET", f"{BASE}/cases/{case_id}/report?language=mr", token=tokens["owner"], content_type="application/pdf")
check("farmer Marathi PDF download", status == 200 and farmer_marathi.startswith(b"%PDF"))
check("farmer PDFs use requested language output", farmer_english != farmer_marathi)
check("farmer Marathi PDF has Unicode character map", b"/ToUnicode" in farmer_marathi)
check("farmer Marathi PDF embeds font program", b"/FontFile" in farmer_marathi)
check("farmer PDFs hide technical model details", all(term not in farmer_english + farmer_marathi for term in (b"Model A", b"Model B", b"Model C", b"Model D", b"EfficientNet", b"Rank 1", b"pending_review", b"Case ID")))

passed = sum(results)
total = len(results)
print(f"\n{passed}/{total} tests passed")
print("FINAL VERIFICATION: PASSED" if passed == total else "FINAL VERIFICATION: FAILED")
raise SystemExit(0 if passed == total else 1)
