"""
Attempt to fetch the Kaggle mastitis dataset.
Kaggle requires authentication for direct downloads.
We try the public dataset API and raw file access.
"""
import urllib.request, sys, os

# Try common raw file names for this dataset
# Dataset: https://www.kaggle.com/datasets/amithadityacp/cow-mastitisfrom-milk
# We'll try to find if there's a publicly accessible mirror or cached version

candidates = [
    "https://raw.githubusercontent.com/amithadityacp/cow-mastitis/main/cow_mastitis.csv",
    "https://raw.githubusercontent.com/amithadityacp/cow-mastitis/main/mastitis.csv",
]

for url in candidates:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "BoviCare/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            content = r.read().decode("utf-8")
            lines = content.strip().split("\n")
            print(f"FOUND at {url}")
            print(f"Rows: {len(lines)}")
            print(f"Header: {lines[0][:300]}")
            sys.exit(0)
    except Exception as e:
        print(f"Not at {url}: {e}")

print("\nKaggle dataset requires authentication - cannot download directly.")
print("Checking if dataset was manually placed in ml/data/...")

data_path = os.path.join(os.path.dirname(__file__), "ml", "data")
if os.path.exists(data_path):
    print("Files in ml/data/:", os.listdir(data_path))
else:
    print("ml/data/ does not exist yet.")
