
from pathlib import Path
import pandas as pd
import pyarrow.dataset as ds
import pyarrow.parquet as pq


def read_parquet_safe(path, columns=None):
    table = pq.read_table(path, columns=columns)
    table = table.replace_schema_metadata(None)  # ignore les métadonnées pandas
    return table.to_pandas()

# Répertoire de lecture et de sortie
DATA_DIR = Path("data")
OUTPUT_FILE = DATA_DIR / "films_merged.parquet"

print("Chargement des données...")

# Chargement des tables
print("Chargement TMDB")
tmdb = read_parquet_safe(DATA_DIR / "tmdb_movies_10k.parquet")



print("Chargement name.basics")
names = read_parquet_safe(
    DATA_DIR / "name.basics.parquet",
    columns=["nconst", "primaryName"]
)

names["nconst"] = names["nconst"].astype("string").str.strip()
print("Chargement basics")
basics = read_parquet_safe(
    DATA_DIR / "title.basics.parquet",
    columns=[
        "tconst", "titleType", "primaryTitle",
        "originalTitle", "startYear",
        "runtimeMinutes", "genres"
    ]
)

print("Chargement ratings")
ratings = read_parquet_safe(DATA_DIR / "title.ratings.parquet")

print("Chargement crew")
crew = read_parquet_safe(DATA_DIR / "title.crew.parquet")


# Conversion des identifiants des réalisateurs en noms
print("\nRécupération des noms des réalisateurs...")

name_dict = names.set_index("nconst")["primaryName"].to_dict() #crée un dictionnaire avec clé les identifiants et comme valeur les noms

name_dict = names.set_index("nconst")["primaryName"].to_dict()

def ids_to_names(x):
    """
    Renvoie les noms des personnes à partir de leurs identifiants nconst.
    """

    if not isinstance(x, str) or x == r"\N":
        return []

    ids = x.split(",")

    noms = []

    for identifiant in ids:
        nom = name_dict.get(identifiant)
        noms.append(nom)

    return noms

crew["directors"] = crew["directors"].apply(ids_to_names)
crew["writers"] = crew["writers"].apply(ids_to_names)

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
].copy()

# Tri par ordre d'importance IMDb
principals = principals.sort_values(["tconst", "ordering"])

# Création d'une liste d'identifiants d'acteurs par film
principals_grouped = (
    principals
    .groupby("tconst")["nconst"]
    .apply(lambda x: ",".join(x.dropna().astype(str)))
    .reset_index(name="principals")
)

# Conversion des identifiants des acteurs en noms
principals_grouped["principals"] = principals_grouped["principals"].apply(ids_to_names)


print("\nJointure")
films = tmdb.merge(
    basics,
    how="left",
    left_on="imdb_id",
    right_on="tconst",
    validate="one_to_one"
)


films = films.merge(
    ratings,
    how="left",
    on="tconst",
    validate="one_to_one"
)


films = films.merge(
    crew,
    how="left",
    on="tconst",
    validate="one_to_one"
)


films = films.merge(
    principals_grouped,
    how="left",
    on="tconst",
    validate="one_to_one"
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

#Suppressiones colonnes inutiles qui font doublon 

colonnes_a_supprimer = [
    "tconst",                 
    "runtimeMinutes_IMDb",    
    "originalTitle_IMDb",     
]

films = films.drop(
    columns=colonnes_a_supprimer
)

# Export
films.to_parquet(OUTPUT_FILE, index=False)

print(f"\nFichier enregistré : {OUTPUT_FILE}")
print("Jointure terminée avec succès !")
