import pandas as pd

df = pd.read_csv("cow_milk_mastitis_dataset.csv")
print(f"Shape: {df.shape}")
print(f"\nColumns ({len(df.columns)}): {list(df.columns)}")
print(f"\nDtypes:\n{df.dtypes}")
print(f"\nMissing values:\n{df.isnull().sum()}")
print(f"\nFirst 3 rows:\n{df.head(3).to_string()}")
print(f"\nDescribe:\n{df.describe(include='all').to_string()}")

# Find target column (last or any non-numeric)
for col in df.columns:
    if df[col].dtype == object or df[col].nunique() < 10:
        print(f"\nPotential target '{col}' value counts:\n{df[col].value_counts()}")
