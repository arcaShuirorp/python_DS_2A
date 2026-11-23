import pandas as pd

df = pd.read_parquet("data/films_merged.parquet")

top_20 = df.sort_values(
    by="numVotes_IMDb",
    ascending=False
).head(20)

print(df[["id","imdb_id", "title", "release_date", "runtime"]].head(100))