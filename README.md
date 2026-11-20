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
├── synthese.ipynb
├── data/                                   # Dossier généré contenant les données générées
└── Script/
    ├── code.py
    ├── fetch_TMDB.py                       # Collecte des films via l'API TMDB
    └── test.ipynb
```


## Installation

### Windows 
```bash
git clone https://github.com/[username]/[repo].git
cd [repo]
python -m pip install -r requirements.txt 
```


## Configuration

Le projet utilise `tmdbv3api` qui permet de réaliser des appels API à la base de données TMDb à condition de posséder une clé API TMDb.

Voir la documentation de `tmdbv3api` [ici](https://github.com/AnthonyBloomer/tmdbv3api).

Voir la documentation API [ici](https://developer.themoviedb.org/docs/getting-started).

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

*TODO: décrire la table ?*
