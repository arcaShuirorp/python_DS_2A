import pandas as pd
import matplotlib.pyplot as plt


def plot_films_par_annee(films):
    annees = pd.to_numeric(films["startYear_IMDb"], errors="coerce")
    if annees.notna().sum() == 0 and "release_date" in films.columns:
        annees = pd.to_datetime(films["release_date"], errors="coerce").dt.year

    par_an = annees.dropna().astype(int).value_counts().sort_index()

    plt.figure(figsize=(12, 5))
    plt.bar(par_an.index, par_an.values, width=0.9)
    plt.title("Nombre de films par année de sortie")
    plt.xlabel("Année")
    plt.ylabel("Nombre de films")
    plt.tight_layout()
    plt.show()



def plot_notes_imdb_tmdb(films):
    imdb = pd.to_numeric(films["averageRating_IMDb"], errors="coerce")
    tmdb = pd.to_numeric(films["vote_average_TMDB"], errors="coerce")
    tmdb = tmdb.where(tmdb > 0)  # les 0 de TMDB = films sans vote

    # Corrélation sur les films ayant les deux notes
    mask = imdb.notna() & tmdb.notna()
    corr = imdb[mask].corr(tmdb[mask])
    print(f"Films avec les deux notes : {mask.sum():,}")
    print(f"Corrélation IMDb / TMDB : {corr:.3f}")

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # Distribution des notes IMDb
    axes[0].hist(imdb.dropna(), bins=40)
    axes[0].set_title("Distribution des notes IMDb")
    axes[0].set_xlabel("Note")
    axes[0].set_ylabel("Nombre de films")

    # Distribution des notes TMDB
    axes[1].hist(tmdb.dropna(), bins=40, color="tab:orange")
    axes[1].set_title("Distribution des notes TMDB")
    axes[1].set_xlabel("Note")

    # Corrélation
    axes[2].scatter(imdb[mask], tmdb[mask], s=5, alpha=0.3)
    axes[2].plot([0, 10], [0, 10], color="red", linestyle="--", label="y = x")
    axes[2].set_title(f"IMDb vs TMDB (corr = {corr:.2f})")
    axes[2].set_xlabel("Note IMDb")
    axes[2].set_ylabel("Note TMDB")
    axes[2].legend()

    plt.tight_layout()
    plt.show()
    






