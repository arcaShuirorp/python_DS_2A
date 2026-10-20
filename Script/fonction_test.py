def fetch_movie_details(movie_id):
    try:
        details = movie_api.details(movie_id)

        return {
            # --- Informations d'Identification et de Base ---
            "id": getattr(details, "id", None),
            "imdb_id": getattr(details, "imdb_id", None),
            "title": getattr(details, "title", None),
            "original_title": getattr(details, "original_title", None),
            "original_language": getattr(details, "original_language", None),
            "tagline": getattr(details, "tagline", None),
            "overview": getattr(details, "overview", None),
            "homepage": getattr(details, "homepage", None),
            
            # --- Dates, Durée et Statut ---
            "release_date": getattr(details, "release_date", None),
            "runtime": getattr(details, "runtime", None),  # En minutes
            "status": getattr(
                details, "status", None
            ),  # Ex: Released, Rumored, Post Production
            # --- Données Financières ---
            "budget": getattr(details, "budget", None),  # En USD
            "revenue": getattr(details, "revenue", None),  # En USD
            # --- Statistiques et Popularité ---
            "popularity": getattr(details, "popularity", None),
            "vote_average": getattr(details, "vote_average", None),  # Note sur 10
            "vote_count": getattr(details, "vote_count", None),
            # --- Contenu Adulte ---
            "adult": getattr(details, "adult", None),
            "video": getattr(
                details, "video", None
            ),  # True s'il y a une vidéo principale associée
            # --- Images (Chemins relatifs à compléter avec l'URL de base TMDb) ---
            "poster_path": getattr(details, "poster_path", None),
            "backdrop_path": getattr(details, "backdrop_path", None),
            # --- Listes et Données Structurées (Listes d'objets ou dictionnaires) ---
            "genres": [
                g["name"] for g in getattr(details, "genres", [])
            ],  # Liste de chaînes (ex: ['Action', 'Sci-Fi'])
            "production_companies": [
                c["name"] for c in getattr(details, "production_companies", [])
            ],
            "production_countries": [
                c["iso_3166_1"]
                for c in getattr(details, "production_countries", [])
            ],  # Codes pays (ex: 'US', 'FR')
            "spoken_languages": [
                l["iso_639_1"] for l in getattr(details, "spoken_languages", [])
            ],  # Codes langues (ex: 'en', 'fr')
            # --- Collection ---
            "belongs_to_collection_id": (
                details.belongs_to_collection.get("id")
                if getattr(details, "belongs_to_collection", None)
                else None
            ),
            "belongs_to_collection_name": (
                details.belongs_to_collection.get("name")
                if getattr(details, "belongs_to_collection", None)
                else None
            ),
        }
    except Exception:
        # En cas d'erreur (ex: film introuvable, problème réseau), on retourne un dictionnaire vide ou rempli de None
        return {}
