
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import requests

from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential
from tmdbv3api import TMDb, Movie
from tqdm import tqdm


# --------------------------------------------------
# PARAMÈTRES
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

load_dotenv(BASE_DIR / ".env", override=True)
API_KEY = os.environ["API_tmdb"]

NB_FILMS = 20000
NB_CANDIDATS = 11000
THREADS = 20
RANDOM_STATE = 42

BATCH_SIZE = 2000 #On fait bout à bout pour sauvegarder auy fur et à mesure

CANDIDATES_FILE = DATA_DIR / "tmdb_candidates_imdb.parquet"
MAPPING_FILE = DATA_DIR / "tmdb_id_mapping.parquet"
CHECKPOINT_FILE = DATA_DIR / "tmdb_details_checkpoint.parquet"
OUTPUT_FILE = DATA_DIR / "tmdb_movies_10k.parquet"


# --------------------------------------------------
# CONNEXION TMDB
# --------------------------------------------------

tmdb = TMDb()
tmdb.api_key = API_KEY

movie_api = Movie()


# --------------------------------------------------
# RECHERCHE D'UN FILM AVEC SON IMDB ID
# --------------------------------------------------

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
def find_tmdb_id(imdb_id):

    url = f"https://api.themoviedb.org/3/find/{imdb_id}"

    params = {
        "api_key": API_KEY,
        "external_source": "imdb_id"
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    results = response.json().get("movie_results", [])

    if results:
        return results[0]["id"]

    return None


def safe_find_tmdb_id(imdb_id):

    try:
        tmdb_id = find_tmdb_id(imdb_id)

        return {
            "imdb_id": imdb_id,
            "tmdb_id": tmdb_id,
            "status": "found" if tmdb_id is not None else "not_found"
        }

    except Exception as e:

        print(f"Erreur recherche {imdb_id} : {e}")

        return {
            "imdb_id": imdb_id,
            "tmdb_id": None,
            "status": "error"
        }


# --------------------------------------------------
# RÉCUPÉRATION DES DÉTAILS D'UN FILM
# --------------------------------------------------

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
def fetch_movie_details(movie_id):

    details = movie_api.details(movie_id)

    return {
        "id": details.id,
        "imdb_id": details.imdb_id,
        "title": details.title,
        "original_title": details.original_title,
        "original_language": details.original_language,
        "tagline": details.tagline,
        "overview": details.overview,
        "homepage": details.homepage,
        "release_date": details.release_date,
        "runtime": details.runtime,
        "status": details.status,
        "budget": details.budget,
        "revenue": details.revenue,
        "popularity": details.popularity,
        "vote_average": details.vote_average,
        "vote_count": details.vote_count,
        "adult": details.adult,
        "video": details.video,
        "poster_path": details.poster_path,
        "backdrop_path": details.backdrop_path,
        "genres": [g["name"] for g in details.genres],
        "production_companies": [
            c["name"] for c in details.production_companies
        ],
        "production_countries": [
            c["name"] for c in details.production_countries
        ],
        "spoken_languages": [
            l["english_name"] for l in details.spoken_languages
        ],
        "collection_id": (
            details.belongs_to_collection["id"]
            if details.belongs_to_collection else None
        ),
        "collection_name": (
            details.belongs_to_collection["name"]
            if details.belongs_to_collection else None
        )
    }


def safe_fetch_movie_details(movie_id):

    try:
        return fetch_movie_details(movie_id)

    except Exception as e:

        print(f"Erreur détails film {movie_id} : {e}")

        return None


# --------------------------------------------------
# 1. CONSTITUTION DE L'ÉCHANTILLON IMDb
# --------------------------------------------------

def prepare_candidates():

    if CANDIDATES_FILE.exists():

        print("Échantillon IMDb déjà existant : chargement...")

        return pd.read_parquet(CANDIDATES_FILE)

    print("Chargement des fichiers IMDb...")

    basics = pd.read_parquet(
        DATA_DIR / "title.basics.parquet"
    )

    ratings = pd.read_parquet(
        DATA_DIR / "title.ratings.parquet"
    )

    # Garder uniquement les longs-métrages
    basics = basics[basics["titleType"] == "movie"].copy()

    # Convertir la durée en numérique
    basics["runtimeMinutes"] = pd.to_numeric(
        basics["runtimeMinutes"], errors="coerce"
    )

    # Convertir le nombre de votes en numérique
    ratings["numVotes"] = pd.to_numeric(
        ratings["numVotes"], errors="coerce"
    )

    # Films de plus de 60 minutes
    basics = basics[basics["runtimeMinutes"] > 60]

    # Films ayant au moins 1000 votes IMDb
    ratings = ratings[ratings["numVotes"] >= 1000]

    # Associer les deux fichiers
    films = basics.merge(ratings, on="tconst")

    print(f"Films IMDb respectant les critères : {len(films)}")

    # Tirage aléatoire reproductible
    candidats = films.sample(
        n=min(NB_CANDIDATS, len(films)),
        random_state=RANDOM_STATE
    )

    # Sauvegarder l'échantillon pour les prochaines exécutions
    candidats.to_parquet(
        CANDIDATES_FILE,
        index=False
    )

    print(f"Candidats sauvegardés : {len(candidats)}")

    return candidats


# --------------------------------------------------
# 2. RECHERCHE DES IDENTIFIANTS TMDB
# --------------------------------------------------

def get_tmdb_ids(imdb_ids):

    if MAPPING_FILE.exists():

        mapping = pd.read_parquet(MAPPING_FILE)

        print(
            f"Correspondances déjà sauvegardées : {len(mapping)}"
        )

    else:

        mapping = pd.DataFrame(
            columns=["imdb_id", "tmdb_id", "status"]
        )

    # Identifier les IMDb IDs déjà traités
    ids_deja_traites = set(mapping["imdb_id"])

    # Ne rechercher que les identifiants manquants
    ids_restants = [
        imdb_id for imdb_id in imdb_ids
        if imdb_id not in ids_deja_traites
    ]

    print(f"Identifiants IMDb restant à rechercher : {len(ids_restants)}")

    # Recherche par lots pour sauvegarder progressivement
    for debut in range(0, len(ids_restants), BATCH_SIZE):

        batch = ids_restants[debut:debut + BATCH_SIZE]

        with ThreadPoolExecutor(max_workers=THREADS) as executor:

            resultats = list(
                tqdm(
                    executor.map(safe_find_tmdb_id, batch),
                    total=len(batch),
                    desc="Recherche des identifiants TMDb"
                )
            )

        nouveaux = pd.DataFrame(resultats)

        # Ne pas enregistrer les erreurs temporaires :
        # elles pourront être retentées au prochain lancement.
        nouveaux = nouveaux[nouveaux["status"] != "error"]

        mapping = pd.concat(
            [mapping, nouveaux],
            ignore_index=True
        )

        # Sauvegarde immédiate des correspondances trouvées
        mapping.to_parquet(
            MAPPING_FILE,
            index=False
        )

    # Garder uniquement les identifiants TMDb trouvés
    tmdb_ids = mapping.loc[
        mapping["status"] == "found", "tmdb_id"
    ].dropna()

    # Supprimer les doublons et trier
    tmdb_ids = sorted(set(tmdb_ids.astype(int)))

    print(f"\nIdentifiants TMDb trouvés : {len(tmdb_ids)}")

    return tmdb_ids


# --------------------------------------------------
# 3. RÉCUPÉRATION DES DÉTAILS TMDB
# --------------------------------------------------

def get_movie_details(tmdb_ids):

    if CHECKPOINT_FILE.exists():

        df = pd.read_parquet(CHECKPOINT_FILE)

        print(f"Détails déjà sauvegardés : {len(df)}")

    else:

        df = pd.DataFrame()

    # Identifier les films dont les détails sont déjà récupérés
    ids_deja_recuperes = (
        set(df["id"].dropna().astype(int))
        if not df.empty else set()
    )

    # Ne récupérer que les films manquants
    ids_restants = [
        movie_id for movie_id in tmdb_ids
        if movie_id not in ids_deja_recuperes
    ]

    print(f"Films restant à récupérer : {len(ids_restants)}")

    # Récupération par lots
    for debut in range(0, len(ids_restants), BATCH_SIZE):

        batch = ids_restants[debut:debut + BATCH_SIZE]

        with ThreadPoolExecutor(max_workers=THREADS) as executor:

            resultats = list(
                tqdm(
                    executor.map(safe_fetch_movie_details, batch),
                    total=len(batch),
                    desc="Détails des films"
                )
            )

        nouveaux = pd.DataFrame([
            film for film in resultats
            if film is not None
        ])

        if not nouveaux.empty:

            df = pd.concat(
                [df, nouveaux],
                ignore_index=True
            )

            df = df.drop_duplicates(subset="id")

            # Sauvegarde intermédiaire
            df.to_parquet(
                CHECKPOINT_FILE,
                index=False
            )

        print(
            f"Checkpoint : {len(df)} films sauvegardés"
        )

    return df


# --------------------------------------------------
# 4. PROGRAMME PRINCIPAL
# --------------------------------------------------

def main():

    # Étape 1 : sélectionner les candidats IMDb
    candidats = prepare_candidates()

    imdb_ids = candidats["tconst"].tolist()

    # Étape 2 : retrouver les identifiants TMDb
    tmdb_ids = get_tmdb_ids(imdb_ids)

    # Étape 3 : récupérer les détails des films
    df = get_movie_details(tmdb_ids)

    # Étape 4 : filtrer les films de plus d'une heure
    df = df[df["runtime"] > 60].copy()

    # Supprimer les doublons
    df = df.drop_duplicates(subset="id")

    # Garder au maximum 10 000 films
    if len(df) > NB_FILMS:

        df = df.sample(
            n=NB_FILMS,
            random_state=RANDOM_STATE
        )

    # Enregistrer le fichier final
    df.to_parquet(
        OUTPUT_FILE,
        index=False
    )

    print("\n------------------------------")
    print("RÉCUPÉRATION TERMINÉE")
    print("------------------------------")

    print(f"Nombre de films : {len(df)}")
    print(f"Identifiants TMDb : {len(tmdb_ids)}")
    print(f"Fichier final : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
