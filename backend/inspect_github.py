import urllib.request, json, sys, os

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "BoviCare/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())

BASE = "https://api.github.com/repos/thyagarajank/Cattle-disease-prediction-using-Machine-Learning"

print("=== Root contents ===")
try:
    items = get(f"{BASE}/contents/")
    for f in items:
        print(f["type"], f["name"], f.get("size", ""))
except Exception as e:
    print("ERROR:", e)
    sys.exit(1)

print("\n=== Dataset dir ===")
try:
    items = get(f"{BASE}/contents/Dataset")
    for f in items:
        print(f["type"], f["name"], f.get("size", ""), f.get("download_url", ""))
except Exception as e:
    print("ERROR:", e)

print("\n=== Download Training.csv ===")
try:
    raw_url = "https://raw.githubusercontent.com/thyagarajank/Cattle-disease-prediction-using-Machine-Learning/main/Training.csv"
    req = urllib.request.Request(raw_url, headers={"User-Agent": "BoviCare/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        content = r.read().decode("utf-8")
    lines = content.strip().split("\n")
    print(f"Rows (incl header): {len(lines)}")
    print(f"Header: {lines[0][:300]}")
    print(f"Row 1:  {lines[1][:300]}")
    print(f"Row 2:  {lines[2][:300]}")
except Exception as e:
    print("ERROR:", e)

print("\n=== Download Testing.csv ===")
try:
    raw_url = "https://raw.githubusercontent.com/thyagarajank/Cattle-disease-prediction-using-Machine-Learning/main/Testing.csv"
    req = urllib.request.Request(raw_url, headers={"User-Agent": "BoviCare/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        content = r.read().decode("utf-8")
    lines = content.strip().split("\n")
    print(f"Rows (incl header): {len(lines)}")
    print(f"Header: {lines[0][:300]}")
except Exception as e:
    print("ERROR:", e)
