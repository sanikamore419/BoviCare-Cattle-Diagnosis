"""Phase 9 verification for private case images and high-risk notifications."""
import json
import os
import sqlite3
import struct
import time
import urllib.error
import urllib.request
import zlib
from pathlib import Path

API_ROOT = os.environ.get("BOVICARE_API_ROOT", "http://localhost:8000/api")
BASE = f"{API_ROOT}/v1"
AUTH = API_ROOT
TS = int(time.time())
TEST_PASSWORD = os.environ.get("BOVICARE_TEST_PASSWORD", "Pass1234")
DB_PATH = Path(__file__).with_name("bovicare.db")


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
            if response.headers.get_content_type() == "application/json" and raw:
                return response.status, json.loads(raw)
            return response.status, raw
    except urllib.error.HTTPError as error:
        try:
            return error.code, json.loads(error.read())
        except Exception:
            return error.code, {}


def png_bytes(width=8, height=8):
    def chunk(name, payload):
        return struct.pack(">I", len(payload)) + name + payload + struct.pack(">I", zlib.crc32(name + payload) & 0xFFFFFFFF)
    raw = b"".join(b"\x00" + bytes([100, 150, 80]) * width for _ in range(height))
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def multipart(url, fields, filename, mime, payload, token=None):
    boundary = b"BoviCarePhase9Boundary"
    parts = []
    for key, value in fields.items():
        parts.append(b"--" + boundary + b"\r\n" + f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode() + str(value).encode() + b"\r\n")
    parts.append(b"--" + boundary + b"\r\n" + f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode() + f"Content-Type: {mime}\r\n\r\n".encode() + payload + b"\r\n")
    body = b"".join(parts) + b"--" + boundary + b"--\r\n"
    return req("POST", url, token=token, data=body, content_type=f"multipart/form-data; boundary={boundary.decode()}")


results = []

def check(label, condition):
    ok = bool(condition)
    results.append(ok)
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}")


# Setup two farmers and one doctor.
tokens = {}
for role, name in (("farmer", "owner"), ("farmer", "other"), ("doctor", "doctor")):
    req("POST", f"{AUTH}/auth/register", {"name": f"P9 {name}", "email": f"p9_{name}_{TS}@example.com", "password": TEST_PASSWORD, "role": role})
    status, data = req("POST", f"{AUTH}/auth/login", {"email": f"p9_{name}_{TS}@example.com", "password": TEST_PASSWORD})
    check(f"{name} login", status == 200 and bool(data.get("access_token")))
    tokens[name] = data.get("access_token", "")

status, cattle = req("POST", f"{BASE}/cattle", {"tag_number": f"P9-COW-{TS}", "sex": "female", "breed": "Holstein"}, tokens["owner"])
check("owner creates cattle", status == 201)
cattle_id = cattle.get("id")
status, case = req("POST", f"{BASE}/cases/triage", {"cattle_tag": f"P9-COW-{TS}", "cattle_id": cattle_id, "symptoms": ["difficulty breathing"]}, tokens["owner"])
check("high-risk case created", status == 201 and case.get("risk_level") == "high")
case_id = case.get("id")

print("\n-- Image security and persistence --")
png = png_bytes()
status, prediction = multipart(f"{BASE}/predictions/image", {"model": "cattle", "case_id": case_id, "cattle_id": cattle_id}, "../../unsafe.png", "image/png", png, tokens["owner"])
check("valid authenticated image upload succeeds", status == 200 and prediction.get("model") == "cattle_image_classifier")
status, _ = multipart(f"{BASE}/predictions/image", {"case_id": case_id}, "note.txt", "text/plain", b"not an image", tokens["owner"])
check("invalid file type rejected", status == 415)
status, _ = multipart(f"{BASE}/predictions/image", {"case_id": case_id}, "large.png", "image/png", b"0" * (10 * 1024 * 1024 + 1), tokens["owner"])
check("oversized upload rejected", status == 413)
status, _ = req("GET", f"{BASE}/cases/{case_id}/image")
check("unauthenticated image access rejected", status == 401)
status, image_bytes = req("GET", f"{BASE}/cases/{case_id}/image", token=tokens["owner"], content_type="image/png")
check("owning farmer image access succeeds", status == 200 and image_bytes.startswith(b"\x89PNG"))
status, _ = req("GET", f"{BASE}/cases/{case_id}/image", token=tokens["other"])
check("different farmer image access forbidden", status == 403)
status, _ = req("GET", f"{BASE}/cases/{case_id}/image", token=tokens["doctor"])
check("doctor image access succeeds", status == 200)
status, _ = req("GET", f"{BASE}/cases/99999999/image", token=tokens["doctor"])
check("nonexistent image case returns 404", status == 404)

with sqlite3.connect(DB_PATH) as connection:
    row = connection.execute("SELECT stored_filename, case_id, cattle_id FROM case_images WHERE case_id = ?", (case_id,)).fetchone()
check("image metadata links case and cattle", row is not None and row[1] == case_id and row[2] == cattle_id)
from app.core.config import get_settings

image_file = Path(get_settings().upload_dir) / row[0] if row else Path("missing")
check("image file is persisted", image_file.resolve().is_file())
check("server filename ignores traversal input", row is not None and ".." not in row[0] and "/" not in row[0] and "\\" not in row[0])
status, _ = req("GET", f"{BASE}/cases/{case_id}/predictions", token=tokens["owner"])
check("image remains available after prediction workflow", status == 200)

print("\n-- Notifications --")
status, notifications = req("GET", f"{BASE}/cases/{case_id}/notifications", token=tokens["doctor"])
check("high-risk case creates notification event", status == 200 and len(notifications) >= 1)
if notifications:
    check("notification status is explicit mock", notifications[0].get("status") == "mock")
    check("notification targets doctor role", notifications[0].get("target_role") == "doctor")
status, normal_case = req("POST", f"{BASE}/cases/triage", {"cattle_tag": f"P9-NORMAL-{TS}", "symptoms": ["coughing"]}, tokens["owner"])
normal_id = normal_case.get("id")
status, normal_notifications = req("GET", f"{BASE}/cases/{normal_id}/notifications", token=tokens["doctor"])
check("non-high-risk case creates no notification", status == 200 and normal_notifications == [])
check("notification event avoids farmer personal data", notifications == [] or all("email" not in json.dumps(item).lower() and "phone" not in json.dumps(item).lower() for item in notifications))

from app.services.image_storage import image_path
try:
    image_path("../bovicare.db")
    traversal_blocked = False
except Exception:
    traversal_blocked = True
check("path traversal is rejected", traversal_blocked)

passed = sum(results)
total = len(results)
print(f"\n{passed}/{total} tests passed")
print("Phase 9: VERIFIED" if passed == total else "Phase 9: FAILURES DETECTED")
raise SystemExit(0 if passed == total else 1)
