import pandas as pd



df = pd.read_parquet("data/films_merged.parquet")

print(df.columns)
print(df.head())

print(len(df))