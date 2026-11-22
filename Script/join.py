from pathlib import Path
import pandas as pd
import pyarrow.dataset as ds

# Répertoire de lecture et de sortie
DATA_DIR = Path("data")
OUTPUT_FILE = DATA_DIR / "films_merged.parquet"

print("Chargement des données...")

# Chargement des tables
print("Chargement TMDB")
tmdb = pd.read_parquet(DATA_DIR / "tmdb_movies_10k.parquet")

print("Chargement basics")
basics = pd.read_parquet(
    DATA_DIR / "title.basics.parquet",
    columns=[
        "tconst", "titleType", "primaryTitle",
        "originalTitle", "startYear",
        "runtimeMinutes", "genres"
    ]
)

print("Chargement ratings")
ratings = pd.read_parquet(DATA_DIR / "title.ratings.parquet")

print("Chargement crew")
crew = pd.read_parquet(DATA_DIR / "title.crew.parquet")

# Préparation des identifiants
tmdb["imdb_id"] = tmdb["imdb_id"].astype("string").str.strip()

for df in [basics, ratings, crew]:
    df["tconst"] = df["tconst"].astype("string").str.strip()

# Chargement des intervenants IMDb
print("Chargement des intervenants IMDb...")

# Récupération des identifiants IMDb présents dans TMDB
imdb_ids = tmdb["imdb_id"].dropna().astype(str).str.strip().unique().tolist()

# On cherche à récupérer le cast des films avec le fichier principals pour ce faire on garde 
dataset = ds.dataset(
    DATA_DIR / "title.principals.parquet",
    format="parquet"
)

# Filtrage pour ne garder que les films de notre échantillon TMDB
principals = dataset.to_table(
    columns=[
        "tconst", "ordering", "nconst",
        "category", "job", "characters"
    ],
    filter=ds.field("tconst").isin(imdb_ids)
).to_pandas()

principals["tconst"] = principals["tconst"].astype("string").str.strip()

# Agrégation du casting par film
print("\nAgrégation du casting...")

# On conserve uniquement les acteurs et actrices
principals = principals[
    principals["category"].isin(["actor", "actress"])
]

# Tri par ordre d'importance IMDb
principals = principals.sort_values(["tconst", "ordering"])

# Création d'une liste d'identifiants d'acteurs par film
principals_grouped = (
    principals
    .groupby("tconst")["nconst"]
    .apply(list)
    .reset_index(name="principals")
)

# Affichage dimensions
print(f"TMDB : {len(tmdb):,} films")
print(f"IMDb basics : {len(basics):,} lignes")
print(f"IMDb ratings : {len(ratings):,} lignes")
print(f"IMDb crew : {len(crew):,} lignes")
print(f"IMDb principals filtrés : {len(principals):,} lignes")



print("\nJointure")
films = tmdb.merge(
    basics,
    how="left",
    left_on="imdb_id",
    right_on="tconst",
    validate="many_to_one"
)

films = films.merge(
    ratings,
    how="left",
    on="tconst",
    validate="many_to_one"
)

films = films.merge(
    crew,
    how="left",
    on="tconst",
    validate="many_to_one"
)

films = films.merge(
    principals_grouped,
    how="left",
    on="tconst",
    validate="many_to_one"
)

# Renommage des colonnes pour identifier leur source
films = films.rename(columns={
    "vote_average": "vote_average_TMDB",
    "vote_count": "vote_count_TMDB",
    "genres_x": "genres_TMDB",

    "averageRating": "averageRating_IMDb",
    "numVotes": "numVotes_IMDb",
    "genres_y": "genres_IMDb",
    "runtimeMinutes": "runtimeMinutes_IMDb",
    "startYear": "startYear_IMDb",
    "titleType": "titleType_IMDb",
    "primaryTitle": "primaryTitle_IMDb",
    "originalTitle": "originalTitle_IMDb",
    "directors": "directors_IMDb",
    "writers": "writers_IMDb",
    "principals": "principals_IMDb"
})

# Export
films.to_parquet(OUTPUT_FILE, index=False)

print(f"\nFichier enregistré : {OUTPUT_FILE}")
print("Jointure terminée avec succès !")