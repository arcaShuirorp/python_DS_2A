# python_DS_2A
#### Projet de Python pour la Data Science (cours du 1er semestre de 2A à l'ENSAE).

Ce projet utilise les bases de données de TMDB (The Movie Data Base), et IMDB pour chercher des corrélations entre le succès commercial et les autres facteurs à dispositions.


## Sources des données utilisées

Les données proviennent des sources suivantes :

TMDB : Accès via API (l'importation n'est pas possible sans clé API obtenable gratuitement sur le site)
       Note du film, nombre de votes, cast, budget, succès commercial etc...

IMDB : Accès via base de données téléchargable 
       Note du film, nombre de votes


## Structure du projet

```text
python_DS_2A
├── .env                                    # Fichier à créer dans lequel importer une clé API
├── .gitignore
├── requirements.txt
├── LICENSE
├── README.md
├── data/                                   # Dossier généré contenant les données générées
|   ├── films_merged.parquet
|   ├── title.crew.parquet
|   ├── title.principals.parquet
|   ├── name.basics.parquet
|   ├── title.ratings.parquet
|   └── tmdb_movies_10k.parquet
└── Script/
    ├── code.py
    ├── Description_base_de_donnee.py       #Quelques stats descriptives sur notre base de donnée
    ├── fetch_TMDB.py                       # Collecte des films via l'API TMDB
    ├── fetch_IMDB.py                       # Collecte des films depuis la base IMDB
    ├── join.py                             # Joint à gauche la base de donnée IMDb sur la base de donnée TMDB
    └── test.ipynb
```


## Installation

### Windows 
```bash
git clone https://github.com/arcaShuirorp/python_DS_2A.git
cd python_DS_2A
python -m pip install -r requirements.txt 
```


## Configuration

Le projet utilise `tmdbv3api` qui permet de réaliser des appels API à la base de données TMDb à condition de posséder une clé API TMDb.

 * Voir la documentation de `tmdbv3api` [ici](https://github.com/AnthonyBloomer/tmdbv3api).

 * Voir la documentation API [ici](https://developer.themoviedb.org/docs/getting-started).

Une fois la clé API obtenue :
1. Créer un fichier `.env` *à la racine du projet* ;
2. Renseigner la clé API selon le format suivant : 

```text
API_tmdb=[cle_api]
```

## Génération des jeux de données

### Jeu de données TMDB

Pour générer le jeu de données à partir de la base TMDB :

```bash
python Script/fetch_TMDB.py
```

Cela génère une table Parquet dans le chemin `data/tmdb_movies_10k.parquet`. 

### Jeu de données IMDB

Pour générer le jeu de données à partir de la base Imdb :

```bash
python Script/fetch_IMDB.py
```

Cela génère quatre tables Parquet dans le chemin `data/title.crew.parquet`,`data/title.principals.parquet`,`data/name.basics.parquet`,`data/title.ratings.parquet`.


### Créer la base donnée finale

Pour créer la base de donnée finale à  partir des données IMDb et TMDB

```bash
python Script/join.py
```

Cela crée une base de donnée finale dans le chemin `data/films_merged.parquet`.

Pour retrouver une description détaillée de la table ainsi construite, voir [par là](Documentation/docu_film_merged.md). 

## Synthèse

Une synthèse du projet est détaillée dans le notebook Python `synthese.ipynb`.
