import os
from pathlib import Path
from dotenv import load_dotenv

from tmdbv3api import TMDb, Movie, Discover
from tenacity import retry, stop_after_attempt, wait_incrementing
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from tqdm import tqdm   # ça fait des barres de progression assez sympas

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env", override = True)

tmdb = TMDb()
tmdb.api_key = os.environ["API_tmdb"]
tmdb.language = 'fr'
tmdb.debug = False

movie_api = Movie()
discover_api = Discover()

# === Valeurs pour les requêtes
MAX_RETRY = 3
WAIT_TIME = 1.5        # Valeur en secondes (s)
MIN_VOTES = 200
MAX_PAGES = 500        # limite imposée par TMDb : 500 pages x 20 films = 10 000 max
THREADS = 10           # nombre d'appels simultanés (TMDb tolère ~40 req/s)


@retry(stop=stop_after_attempt(MAX_RETRY),
       wait=wait_incrementing(start=WAIT_TIME, increment=WAIT_TIME),
       retry_error_callback=lambda x:{})
def fetch_movie_details(movie_id):
    """
    Etant donnée un movie_id, renvoie les détails associés à ce film dans un dictionnaire.

    PS: je laisse la fonction au dessus pour l'instant, mais celle-là marche direct avec un retry et est peut-être
    plus lisible ????
    """

    details = movie_api.details(movie_id)
    # Ces champs correspondent à ceux qui renvoient une valeur unique
    simple_fields = [
            "id", "imdb_id", "title", "original_title", "original_language", "tagline", "overview", "homepage",  # Infos d'identification
            "release_date", "runtime", "status",  # Date, durée et status
            "budget", "revenue",  # Infos financières
            "popularity", "vote_average", "vote_count",  # Statistiques de popularité
            "adult", "video", "poster_path", "backdrop_path"  # Autres données
            ]
    # Ces champs correspondent à ceux qui renvoient une liste de valeurs à parser
    list_fields = {
            "genres": "name",
            "production_companies": "name",
            "production_countries": "iso_3166_1",
            "spoken_languages": "iso_639_1"
            }
    collections = getattr(details, "belongs_to_collection", None) or {}  # Permet de vérifier l'appartenance à une collection

    rows = {field: getattr(details, field, None) for field in simple_fields}
    rows.update({
        field: [item[key] for item in getattr(details, field, None) or []]
        for field, key in list_fields.items()
    })
    rows.update(
        belongs_to_collection_id=collections.get("id"),
        belongs_to_collection_name=collections.get("name")
    )

    return rows


@retry(stop=stop_after_attempt(MAX_RETRY),
       wait=wait_incrementing(start=WAIT_TIME, increment=WAIT_TIME),
       retry_error_callback=lambda x:[])
def fetch_discover_page(page):
    params = {
        "sort_by": "vote_count.desc",
        "vote_count.gte": MIN_VOTES,
        "include_adult": "true",
        "page": page,
    }
    results = discover_api.discover_movies(params)
            
    return [m.id for m in results]


def main():
    # Vérification préemptive pour clé API (en théorie inutile)
    if not tmdb.api_key:
        raise SystemExit("Aucune clé API_tmdb trouvée dans .env")
    
    # Récupération des données
    with ThreadPoolExecutor(THREADS) as pool:
        pages = list(tqdm(pool.map(fetch_discover_page, range(1, MAX_PAGES + 1)),
                          total=MAX_PAGES, desc="Pages"))
        ids = list(dict.fromkeys(i for p in pages for i in p))
        results = list(tqdm(pool.map(fetch_movie_details, ids),
                            total=len(ids), desc="Films"))
    
    rows = [r for r in results if r]
    print(f"{len(rows)}/{len(ids)} films récupérés")
    df = pd.DataFrame(rows)
    df = df.drop_duplicates("id").reset_index(drop=True)  # On vérifie les doublons et on indexe proprement

    OUTPUT_DIR = BASE_DIR / "data"
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    FILE_NAME = "tmdb_movies_10k.parquet"


    df.to_parquet(OUTPUT_DIR / FILE_NAME, index=False)   # On convertit en parquet (plus cool) et on sauvegarde
    print(f"Terminé : {len(df)} films sauvegardés dans {OUTPUT_DIR / FILE_NAME}")
    return df


if __name__ == "__main__":
    df = main()
