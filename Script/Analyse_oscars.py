from pathlib import Path
import pandas as pd
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import statsmodels.api as sm


#### On complète les tables par les informations sur les acteurs

df_reg2 = pd.read_parquet("data/films_merged.parquet")

# Pour pouvoir faire des analyses de données, on transforme les données de la colonne "averageRating_IMDb" en nombres
df_reg2 = df_reg2[['id', 'imdb_id', 'title', 'release_date', 'budget', 'revenue', 'averageRating_IMDb', 'principals_IMDb']]
df_reg2["averageRating_IMDb"] = pd.to_numeric(
    df_reg2["averageRating_IMDb"],
    errors="coerce"
)

df_reg2 = df_reg2.dropna(subset = ["principals_IMDb", "release_date"]) #Il nous faut les noms des acteurs et l'année de sortie du film pour pouvoir faire l'analyse

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



### On complète les tables avec les informations sur la rentabilité des films

df_reg2["budget"] = pd.to_numeric(df_reg2["budget"], errors="coerce")
df_reg2["revenue"] = pd.to_numeric(df_reg2["revenue"], errors="coerce")

# Création des variables de rentabilité
df_reg2["benefice"] = df_reg2["revenue"] - df_reg2["budget"]

df_reg2["ROI"] = np.where(
    df_reg2["budget"] > 0,
    (df_reg2["revenue"] - df_reg2["budget"]) / df_reg2["budget"] * 100,
    np.nan
)


### Liste de films connus pour les étudier à part

liste_films_connus = [
    "Astérix and Obélix : God Save Britannia",
    "OSS 117: Lost in Rio",
    "Avengers: Age of Ultron",
    "Spider-Man: Into the Spider-Verse",
    "Toy Story 3",
    "Once Upon a Time in... Hollywood",
    "Taxi",
    "Star Wars: Episode III - Revenge of the Sith"
]

films_connus = df_reg2[
    df_reg2["title"].isin(liste_films_connus)
].copy()



### Fonctions à utiliser dans la synthèse


def stats():
    stats = df_reg2.groupby("nb_acteurs_oscarises").agg(
        nb_films=("id", "count"),
    ).round(2)
    print(stats)




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


def renta_oscar():

    # stats
    stats_roi = df_reg2[df_reg2["budget"] > 0].groupby("acteur_oscarise").agg(
        nb_films=("id", "count"),
        budget_moyen=("budget", "mean"),
        revenue_moyen=("revenue", "mean"),
        benefice_moyen=("benefice", "mean"),
        ROI_moyen=("ROI", "mean"),
        ROI_median=("ROI", "median")
    ).round(2)

    print(stats_roi)

    fig, ax = plt.subplots(figsize=(12, 7))

    sns.boxplot(
        data=df_reg2[df_reg2["budget"] > 0],
        x="acteur_oscarise",
        y="ROI",
        hue="acteur_oscarise",
        palette={False: "#4C78A8", True: "#F58518"},
        legend=False,
        showfliers=False,
        width=0.5,
        ax=ax
    )

    films_a_afficher = films_connus.dropna(
        subset=["acteur_oscarise", "ROI"]
    )

    couleurs = sns.color_palette("husl", len(liste_films_connus))
    couleurs_par_film = dict(zip(liste_films_connus, couleurs))

    for _, film in films_a_afficher.iterrows():

        x = int(film["acteur_oscarise"])

        ax.scatter(
            x,
            film["ROI"],
            color=couleurs_par_film[film["title"]],
            s=130,
            edgecolor="black",
            linewidth=1,
            zorder=5,
            label=film["title"]
        )


    ax.axhline(0, color="black", linewidth=1.2, linestyle="--", alpha=0.7)

    ax.set_title(
        "Rentabilité selon la présence d'acteurs oscarisés",
        fontsize=16,
        fontweight="bold",
        pad=18
    )

    ax.set_xlabel("Présence d'un acteur oscarisé", fontsize=12)
    ax.set_ylabel("ROI (%)", fontsize=12)

    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Non", "Oui"])
    handles, labels = ax.get_legend_handles_labels()
    elements = dict(zip(labels, handles))

    ax.legend(
        elements.values(),
        elements.keys(),
        bbox_to_anchor=(1.02, 1),
        loc="upper left",
        title="Films connus",
        frameon=False
    )

    sns.despine()
    ax.grid(axis="y", alpha=0.2)

    plt.tight_layout()
    plt.show()


def renta_nb_oscar():

    # statistiques affichées dans la synthèse
    stats_roi = df_reg2[df_reg2["budget"] > 0].groupby("nb_acteurs_oscarises").agg(
        nb_films=("id", "count"),
        budget_moyen=("budget", "mean"),
        revenue_moyen=("revenue", "mean"),
        benefice_moyen=("benefice", "mean"),
        ROI_moyen=("ROI", "mean"),
        ROI_median=("ROI", "median")
    ).round(2)

    print(stats_roi)
    fig, ax = plt.subplots(figsize=(12, 7))

    categories = sorted(df_reg2["nb_acteurs_oscarises"].dropna().unique())

    sns.boxplot(
        data=df_reg2[df_reg2["budget"] > 0],
        x="nb_acteurs_oscarises",
        y="ROI",
        hue="nb_acteurs_oscarises",
        palette="Blues",
        legend=False,
        showfliers=False,
        width=0.5,
        ax=ax
    )

    #Films connus
    films_a_afficher = films_connus.dropna(
        subset=["nb_acteurs_oscarises", "ROI"]
    )

    couleurs = sns.color_palette("husl", len(liste_films_connus))
    couleurs_par_film = dict(zip(liste_films_connus, couleurs))

    for _, film in films_a_afficher.iterrows():

        x = categories.index(film["nb_acteurs_oscarises"])

        ax.scatter(
            x,
            film["ROI"],
            color=couleurs_par_film[film["title"]],
            s=130,
            edgecolor="black",
            linewidth=1,
            zorder=5,
            label=film["title"]
        )

        ax.annotate(
            film["title"],
            (x, film["ROI"]),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8
        )

    ax.axhline(
        0,
        color="black",
        linewidth=1.2,
        linestyle="--",
        alpha=0.7
    )

    ax.set_title(
        "ROI selon le nombre d'acteurs oscarisés",
        fontsize=16,
        fontweight="bold",
        pad=18
    )

    ax.set_xlabel("Nombre d'acteurs oscarisés", fontsize=12)
    ax.set_ylabel("ROI (%)", fontsize=12)

    ax.set_xticks(range(len(categories)))
    ax.set_xticklabels(categories)

    handles, labels = ax.get_legend_handles_labels()
    elements = dict(zip(labels, handles))

    ax.legend(
        elements.values(),
        elements.keys(),
        bbox_to_anchor=(1.02, 1),
        loc="upper left",
        title="Films connus",
        frameon=False
    )

    sns.despine()
    ax.grid(axis="y", alpha=0.2)

    plt.tight_layout()
    plt.show()


def corr_budget_acteurs_osc():

    # statistiques affichées dans la synthèse
    stats_budget = df_reg2[df_reg2["budget"]>0].groupby("nb_acteurs_oscarises").agg(
        nb_films=("id", "count"),
        budget_moyen=("budget", "mean"),
        budget_median=("budget", "median"),
        budget_max=("budget", "max")
    ).round(2)

    print("\nSTATISTIQUES DESCRIPTIVES")
    print(stats_budget)

    # données pour la régression
    df_reg = df_reg2[
        (df_reg2["budget"] > 0) &
        df_reg2["nb_acteurs_oscarises"].notna()
    ].copy()

    df_reg["log_budget"] = np.log(df_reg["budget"])


    X = sm.add_constant(df_reg["nb_acteurs_oscarises"])
    y = df_reg["log_budget"]

    modele = sm.OLS(y, X).fit()

    print("\nRÉSULTATS DE LA RÉGRESSION")
    print(modele.summary())
    print("\nCOEFFICIENTS :")
    print(modele.params)

    
    fig, ax = plt.subplots(figsize=(12, 7))

    categories = sorted(
        df_reg2["nb_acteurs_oscarises"].dropna().unique()
    )

    ax.scatter(
        df_reg["nb_acteurs_oscarises"],
        df_reg["budget"],
        alpha=0.3,
        s=30,
        color="#4C78A8"
    )

    x_ligne = np.linspace(min(categories), max(categories), 100)

    y_ligne = modele.params.iloc[0] + modele.params.iloc[1] * x_ligne

    ax.plot(
        x_ligne,
        np.exp(y_ligne),
        color="red",
        linewidth=2,
        label="Régression linéaire sur log(budget)"
    )

    # Films connus
    films_a_afficher = films_connus.dropna(
        subset=["nb_acteurs_oscarises", "budget"]
    )

    films_a_afficher = films_a_afficher[
        films_a_afficher["budget"] > 0
    ]

    couleurs = sns.color_palette("husl", len(liste_films_connus))
    couleurs_par_film = dict(zip(liste_films_connus, couleurs))

    for _, film in films_a_afficher.iterrows():

        ax.scatter(
            int(film["nb_acteurs_oscarises"]),
            film["budget"],
            color=couleurs_par_film[film["title"]],
            s=130,
            edgecolor="black",
            linewidth=1,
            zorder=5,
            label=film["title"]
        )

    ax.set_yscale("log")

    ax.set_title(
        "Budget selon le nombre d'acteurs oscarisés",
        fontsize=16,
        fontweight="bold",
        pad=18
    )

    ax.set_xlabel("Nombre d'acteurs oscarisés", fontsize=12)
    ax.set_ylabel("Budget", fontsize=12)

    ax.set_xticks(categories)
    ax.set_xticklabels(categories)

    handles, labels = ax.get_legend_handles_labels()
    elements = dict(zip(labels, handles))

    ax.legend(
        elements.values(),
        elements.keys(),
        bbox_to_anchor=(1.02, 1),
        loc="upper left",
        title="Films connus",
        frameon=False
    )

    sns.despine()
    ax.grid(axis="y", alpha=0.2, which="both")

    plt.tight_layout()
    plt.show()



def revenue_et_budget_vs_osc():

    # statistiques descriptives (montrées dans la synthèse)
    stats = df_reg2.groupby("acteur_oscarise").agg(
        nb_films=("id", "count"),
        budget_moyen=("budget", "mean"),
        budget_median=("budget", "median"),
        revenue_moyen=("revenue", "mean"),
        revenue_median=("revenue", "median")
    ).round(2)

    print("\nSTATISTIQUES DESCRIPTIVES")
    print(stats)
    

    # Création des graphiques
    fig, axes = plt.subplots(1, 2, figsize=(15, 7))

    variables = [
        ("budget", "Budget"),
        ("revenue", "Revenus")
    ]

    couleurs_categories = {
        False: "#4C78A8",
        True: "#F58518"
    }

    films_a_afficher = films_connus.dropna(
        subset=["acteur_oscarise", "budget", "revenue"]
    )

    couleurs = sns.color_palette("husl", len(liste_films_connus))
    couleurs_par_film = dict(zip(liste_films_connus, couleurs))

    for ax, (variable, titre) in zip(axes, variables):

        sns.boxplot(
            data=df_reg2,
            x="acteur_oscarise",
            y=variable,
            hue="acteur_oscarise",
            palette=couleurs_categories,
            legend=False,
            showfliers=False,
            width=0.5,
            ax=ax
        )

        # données pour la régression
        df_reg = df_reg2[
            (df_reg2[variable] > 0) &
            df_reg2["acteur_oscarise"].notna()
        ].copy()

        df_reg["log_variable"] = np.log(df_reg[variable])

        X = sm.add_constant(df_reg["acteur_oscarise"].astype(int))
        y = df_reg["log_variable"]

        modele = sm.OLS(y, X).fit()

        print(f"\nRÉSULTATS DE LA RÉGRESSION : {titre.upper()}")
        print(modele.summary())
        print("\nCOEFFICIENTS :")
        print(modele.params)

        x_ligne = np.array([0, 1])

        y_ligne = (
            modele.params.iloc[0] +
            modele.params.iloc[1] * x_ligne
        )

        ax.plot(
            x_ligne,
            np.exp(y_ligne),
            color="red",
            linewidth=2,
            marker="o",
            label="Régression sur log"
        )

        # Films connus
        for _, film in films_a_afficher.iterrows():

            y_film = film[variable]

            if y_film <= 0:
                continue

            ax.scatter(
                int(film["acteur_oscarise"]),
                y_film,
                color=couleurs_par_film[film["title"]],
                s=110,
                edgecolor="black",
                linewidth=1,
                zorder=5,
                label=film["title"]
            )


        ax.set_yscale("log") # échelle logarithmique

        ax.set_title(
            f"{titre} selon la présence d'acteurs oscarisés",
            fontsize=13,
            fontweight="bold",
            pad=15
        )

        ax.set_xlabel("Présence d'un acteur oscarisé", fontsize=11)
        ax.set_ylabel(titre, fontsize=11)

        ax.set_xticks([0, 1])
        ax.set_xticklabels(["Non", "Oui"])

        ax.grid(axis="y", alpha=0.2, which="both")
        sns.despine(ax=ax)

    handles, labels = axes[0].get_legend_handles_labels()
    elements = dict(zip(labels, handles))

    fig.legend(
        elements.values(),
        elements.keys(),
        bbox_to_anchor=(1.02, 1),
        loc="upper left",
        title="Films connus",
        frameon=False
    )

    plt.tight_layout()
    plt.show()
