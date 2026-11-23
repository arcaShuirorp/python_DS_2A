
# Documentation de la base de données `films_merged.parquet`

## 1. Présentation générale

Cette base de données regroupe des informations cinématographiques issues de TMDB et IMDb.

Il s'agit de données sur les 10 000 films les plus votés sur TMDB enrichies par les données de ces films sur IMDb.

L'objectif est d'obtenir une base de données finale à partir de laquelle on peut faire les études statistiques.

## 2. Sources des données
Le lien vers les datasets utilisés pour IMDb est : https://datasets.imdbws.com

Les données issues de TMDB proviennent de son API : https://developer.themoviedb.org/reference/getting-started


| Source | Fichier | Informations apportées |
|:---|:---|:---|
| TMDB | `tmdb_movies_10k.parquet` | Informations générales, budget, recettes, popularité et votes |
| IMDb | `title.basics.parquet` | Titres, année, durée et genres |
| IMDb | `title.ratings.parquet` | Notes et nombre de votes |
| IMDb | `title.crew.parquet` | Réalisateurs et scénaristes |
| IMDb | `title.principals.parquet` | Acteurs et actrices principaux |
| IMDb | `name.basics.parquet` | Noms des personnes |

## 3. Construction de la base

La table TMDB constitue la table principale. Les données IMDb sont intégrées à partir de l'identifiant IMDb (`imdb_id` dans TMDB et `tconst` dans IMDb).

Les principales opérations réalisées sont :
- On récupère les identifiant imdb des 10 000 films TMDB
- Filtrage des données IMDb pour conserver les films de l'échantillon.
- Récupération des noms des acteurs, réalisateurs et scénaristes qui sont des identifiants dans les tables title.crew et title.principals il faut donc aller chercher les noms dans name.basics.
- Fusion des tables à l'aide de jointures à gauche.
- Renommage des colonnes pour distinguer les données TMDB et IMDb.

## 4. Dictionnaire des variables

| Variable | Description |
|:---|:---|
| `id` | Identifiant du film dans TMDB |
| `imdb_id` | Identifiant du film dans IMDb |
| `title` | Titre du film dans TMDB |
| `original_title` | Titre original du film dans TMDB |
| `primaryTitle_IMDb` | Titre principal selon IMDb |
| `titleType_IMDb` | Type de contenu selon IMDb |
| `original_language` | Langue originale du film selon TMDB |
| `tagline` | Phrase d'accroche du film |
| `overview` | Résumé ou synopsis du film |
| `homepage` | Site internet officiel associé au film |
| `release_date` | Date de sortie du film selon TMDB |
| `startYear_IMDb` | Année de sortie selon IMDb |
| `runtime` | Durée du film selon TMDB |
| `status` | Statut du film dans TMDB |
| `adult` | Indique si le film est classé comme contenu adulte |
| `video` | Indique si le contenu est identifié comme une vidéo par TMDB |
| `budget` | Budget du film selon TMDB |
| `revenue` | Recettes du film selon TMDB |
| `popularity` | Indicateur de popularité calculé par TMDB |
| `vote_average_TMDB` | Note moyenne attribuée au film sur TMDB |
| `vote_count_TMDB` | Nombre de votes enregistrés sur TMDB |
| `averageRating_IMDb` | Note moyenne attribuée au film sur IMDb |
| `numVotes_IMDb` | Nombre de votes enregistrés sur IMDb |
| `genres_TMDB` | Genres associés au film selon TMDB |
| `genres_IMDb` | Genres associés au film selon IMDb |
| `poster_path` | Chemin d'accès à l'affiche du film sur TMDB |
| `backdrop_path` | Chemin d'accès à l'image d'arrière-plan du film sur TMDB |
| `production_companies` | Sociétés de production associées au film |
| `production_countries` | Pays de production du film |
| `spoken_languages` | Langues parlées dans le film |
| `belongs_to_collection_id` | Identifiant de la collection TMDB associée au film |
| `belongs_to_collection_name` | Nom de la collection TMDB associée au film |
| `directors_IMDb` | Noms des réalisateurs identifiés par IMDb |
| `writers_IMDb` | Noms des scénaristes identifiés par IMDb |
| `principals_IMDb` | Noms des acteurs et actrices principaux identifiés par IMDb |

## 6. Fichier final

Le fichier final est disponible au format Parquet :

`data/films_merged.parquet`
