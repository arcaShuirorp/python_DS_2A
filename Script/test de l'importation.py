import os
import asyncio
import pandas as pd
from dotenv import load_dotenv
from tmdbv3api import TMDb, Movie, Discover
from fonctions import fetch_movie_details
load_dotenv(override=True)

tmdb = TMDb()
tmdb.api_key = os.environ["API_tmdb"]
tmdb.language = "fr"
tmdb.debug = False  
movie_api = Movie()
discover_api = Discover()

TARGET = 10000
MIN_VOTES = 200
MAX_PAGES = 500        # limite imposée par TMDb : 500 pages x 20 films = 10 000 max
CONCURRENCY = 20       # nombre d'appels simultanés (TMDb tolère ~50 req/s)


# --------------------------------------------------------------------------
# 1)Pour éviter de dépasser la limite de l'API si on l'attend on attend 1. 5 s 
#   quand il y a un problème
# --------------------------------------------------------------------------


def fetch_with_retry(movie_id, retries=3):
    for attempt in range(retries):
        result = fetch_movie_details(movie_id)
        if result:
            return result
        import time
        time.sleep(1.5 * (attempt + 1))
    return {}


# ---------------------------------------------------------------------------
# 3) Récupération des IDs via /discover/movie
# ---------------------------------------------------------------------------

def fetch_discover_page(page):
    params = {
        "sort_by": "vote_count.desc",
        "vote_count.gte": MIN_VOTES,
        "include_adult": "true",
        "page": page,
    }
    for attempt in range(3):
        try:
            results = discover_api.discover_movies(params)
            return [m.id for m in results]
        except Exception:
            import time
            time.sleep(1.5 * (attempt + 1))
    return []


async def collect_movie_ids():
    sem = asyncio.Semaphore(CONCURRENCY) # permet d'éviter de faire trop de tache en même temps et de surbooker l'api

    async def worker(page):
        async with sem:
            return await asyncio.to_thread(fetch_discover_page, page)

    pages = await asyncio.gather(*(worker(p) for p in range(1, MAX_PAGES + 1)))

    ids, seen = [], set()
    for page_ids in pages:
        for movie_id in page_ids:
            if movie_id not in seen:  # dédoublonnage (la pagination peut bouger)
                seen.add(movie_id)
                ids.append(movie_id)
    return ids[:TARGET]


# ---------------------------------------------------------------------------
# 4) Récupération des détails en parallèle
# ---------------------------------------------------------------------------

async def collect_details(movie_ids):
    sem = asyncio.Semaphore(CONCURRENCY)
    done = 0

    async def worker(movie_id):
        nonlocal done
        async with sem:
            data = await asyncio.to_thread(fetch_with_retry, movie_id)
        done += 1
        if done % 500 == 0:
            print(f"{done}/{len(movie_ids)} films traités")
        return data

    results = await asyncio.gather(*(worker(i) for i in movie_ids))
    return [r for r in results if r]


# ---------------------------------------------------------------------------
# 5) Main
# ---------------------------------------------------------------------------
async def main():
    print("Récupération des IDs...")
    movie_ids = await collect_movie_ids()
    print(f"{len(movie_ids)} IDs récupérés")

    print("Récupération des détails...")
    rows = await collect_details(movie_ids)

    df = pd.DataFrame(rows)
    df = df.drop_duplicates("id").reset_index(drop=True) #On verifie les doublons et on index propremetnt

    df.to_csv("tmdb_movies_10k.csv", index=False, encoding="utf-8") #On convertit en csv et on sauvegarde
    print(f"Terminé : {len(df)} films sauvegardés dans tmdb_movies_10k.csv")
    return df


if __name__ == "__main__":
    df = asyncio.run(main())
    