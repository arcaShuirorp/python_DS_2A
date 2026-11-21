import pandas as pd

df = pd.read_parquet("data/title.basics.parquet")
print(df.head())