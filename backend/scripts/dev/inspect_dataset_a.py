import urllib.request, io, sys

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "BoviCare/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")

import pandas as pd

train_url = "https://raw.githubusercontent.com/thyagarajank/Cattle-disease-prediction-using-Machine-Learning/main/Training.csv"
test_url  = "https://raw.githubusercontent.com/thyagarajank/Cattle-disease-prediction-using-Machine-Learning/main/Testing.csv"

print("Fetching Training.csv...")
train_csv = fetch(train_url)
df = pd.read_csv(io.StringIO(train_csv))
print(f"Shape: {df.shape}")
print(f"Columns ({len(df.columns)}): {list(df.columns)}")
print(f"\nLast column (target): {df.columns[-1]}")
print(f"\nTarget value counts:\n{df[df.columns[-1]].value_counts().to_string()}")
print(f"\nMissing values: {df.isnull().sum().sum()}")
print(f"\nFeature dtypes sample:\n{df.dtypes.value_counts()}")
print(f"\nFeature value range (first 5 cols):\n{df.iloc[:, :5].describe()}")

print("\nFetching Testing.csv...")
test_csv = fetch(test_url)
df_test = pd.read_csv(io.StringIO(test_csv))
print(f"Test shape: {df_test.shape}")
print(f"Test target value counts:\n{df_test[df_test.columns[-1]].value_counts().to_string()}")
