import pandas as pd

df = pd.read_parquet("data/tmdb_movies_10k.parquet")

# Afficher les 20 premiers films
print(df[["id", "title", "release_date", "runtime"]].head(20))