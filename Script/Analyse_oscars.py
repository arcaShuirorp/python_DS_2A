from pathlib import Path
import pandas as pd
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt



#### On complète les tables par les informations sur les acteurs

df_reg2 = pd.read_parquet("data/films_merged.parquet")

# Pour pouvoir faire des analyses de données, on transforme les données de la colonne "averageRating_IMDb" en nombres
df_reg2 = df_reg2[['id', 'imdb_id', 'title', 'release_date', 'budget', 'revenue', 'averageRating_IMDb', 'principals_IMDb']]
df_reg2["averageRating_IMDb"] = pd.to_numeric(
    df_reg2["averageRating_IMDb"],
    errors="coerce"
)

df_reg2 = df_reg2.dropna(subset = ["principals_IMDb", "release_date"]) #Il nous faut les noms d'acteurs et l'année de sortie du film pour pouvoir faire l'analyse

df_reg2["release_year"] = pd.to_datetime(
    df_reg2["release_date"],
    errors="coerce"
).dt.year

df_acteurs_osc = pd.read_csv("data/data_oscars_complet.csv")
df_acteurs_osc = df_acteurs_osc[
    (df_acteurs_osc["status"] == "Won") &
    (df_acteurs_osc["award_category"].isin(["Actor", "Actress"]))
]

df_acteurs_osc = df_acteurs_osc[["name", "ceremony_year"]]



def compter_oscarises(liste_acteurs, date):
    n = 0

    for acteur in liste_acteurs:
        if (
            ((df_acteurs_osc["name"] == acteur) &
             (df_acteurs_osc["ceremony_year"] <= date)).any()
        ):
            n += 1

    return n
    

df_reg2["nb_acteurs_oscarises"] = df_reg2.apply(
    lambda row: compter_oscarises(
        row["principals_IMDb"],
        int(row["release_year"])
    ) if pd.notna(row["release_year"]) else 0,
    axis=1
)

df_reg2["acteur_oscarise"] = (df_reg2["nb_acteurs_oscarises"]>0) # False ou True

liste_films_connus = ["Astérix and Obélix : God Save Britannia", 
    "OSS 117: Lost in Rio",
    "Avengers: Age of Ultron",
    "Spider-Man: Into the Spider-Verse",
    "Toy Story 3",
    "Once Upon a Time in... Hollywood",
    "Taxi",
    "Star Wars: Episode III - Revenge of the Sith"]


#####

def note_oscar():

    groupes = [
        groupe["averageRating_IMDb"].dropna().values
        for _, groupe in df_reg2.groupby("nb_acteurs_oscarises")
    ]

    categories = sorted(df_reg2["nb_acteurs_oscarises"].dropna().unique())

    plt.figure(figsize=(12, 7))
    plt.boxplot(groupes, tick_labels=categories)

    plt.xlabel("Nombre d'acteurs oscarisés")
    plt.ylabel("Note moyenne du film")
    plt.title("Note des films selon le nombre d'acteurs oscarisés")
    plt.grid(axis="y", alpha=0.3)

    films_connus = df_reg2[df_reg2["title"].isin(liste_films_connus)]

    # Palette de couleurs
    couleurs = plt.cm.tab10.colors

    # Ajouter chaque film individuellement
    for i, (_, film) in enumerate(films_connus.iterrows()):

        x = categories.index(film["nb_acteurs_oscarises"]) + 1
        y = film["averageRating_IMDb"]

        plt.scatter(
            x, y,
            color=couleurs[i % len(couleurs)],
            s=60,
            zorder=3,
            label=film["title"]
        )

    plt.legend(title="Films connus", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()
    plt.show()


def note_oscar_bin():
    groupes = [
        groupe["averageRating_IMDb"].dropna().values
        for _, groupe in df_reg2.groupby("acteur_oscarise")
    ]

    categories = sorted(df_reg2["acteur_oscarise"].dropna().unique())

    plt.figure(figsize=(12, 7))
    plt.boxplot(groupes, tick_labels=categories)

    plt.xlabel("Acteur oscarisé ou non (True ou False)")
    plt.ylabel("Note moyenne du film")
    plt.title("Note des films selon la présence d'un acteur oscarisé")
    plt.grid(axis="y", alpha=0.3)

    films_connus = df_reg2[df_reg2["title"].isin(liste_films_connus)]

    # Palette de couleurs
    couleurs = plt.cm.tab10.colors

    # Ajouter chaque film individuellement
    for i, (_, film) in enumerate(films_connus.iterrows()):

        x = categories.index(film["acteur_oscarise"]) + 1
        y = film["averageRating_IMDb"]

        plt.scatter(
            x, y,
            color=couleurs[i % len(couleurs)],
            s=60,
            zorder=3,
            label=film["title"]
        )

    plt.legend(title="Films connus", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()
    plt.show()
note_oscar()