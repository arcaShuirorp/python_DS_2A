# python_DS_2A
Projet de Python pour la Data Science (cours du 1er semestre de 2A à l'ENSAE).

Ce projet utilise les bases de données de TMDB (The movie data base), et IMDB pour chercher des corrélations entre le succès commercial et les autres facteurs à dispositions.


#Source de données

Les données proviennent des sources suivantes :

TMDB : Accès via API, l'importation n'est pas possible sans clé API obtenable gratuitement sur le site
       Note des films, nombre de vote, cast, budget, succès commercial etc...

IMDB : Accès via base de donnée téléchargable 
       Note de film et nombre de vote


#Architecture

Ne pas hésiter à installer `tree` dans le terminal pour faciliter la visualisation :

```{bash}
sudo apt update
sudo apt install tree
tree
```

├── python_DS_2A
│   ├── LICENSE
│   ├── README.md
│   └── Script
│       ├── code.py
│       ├── fonctions.py
│       ├── test de l'importation.py            #Importation des données via l'API TMDB 
│       └── test.ipynb
└── synthese.ipynb