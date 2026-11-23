import pandas as pd

df = pd.read_parquet("data/films_merged.parquet")

top = df.sort_values(
    by="numVotes_IMDb",
    ascending=False
)

print(df[df["title"].str.contains("Toy Story", case=False, na=False)][["id", "title", "release_date"]])
