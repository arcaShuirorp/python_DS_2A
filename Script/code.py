import pandas as pd



df = pd.read_parquet("data/tmdb_movies_10k.parquet")

print(df.head())
