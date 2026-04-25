import pandas as pd
import os

filepath = r"d:\talash\backend\qs_rankings\2026 QS World University Rankings 1.3 (For qs.com).xlsx"
df = pd.read_excel(filepath)
print(df.head(10))
print(df.columns)
