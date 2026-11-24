"""
Ce script fait essentiellement la même chose que roi_by_genre.py mais pour séparer 
les revenus et les budgets
"""

# === Importations
import os
from pathlib import Path

from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# === Config

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
if not os.path.exists(DATA_DIR):
    print(f"Le dossier au chemin d'accès {DATA_DIR} n'existe pas. Création en cours...")
    os.makedirs(DATA_DIR)
    print(f"Dossier 'data' créé. Pensez à importer les données nécessaires !")


# === LE CODE.......

df = pd.read_parquet(DATA_DIR / "films_merged.parquet")

def budget_revenue_by_genre(df, sort_by="revenue_median"):
    """Calcule des stats sur les budgets et revenus moyens/médians d'un film par genre de film suffisamment représenté"""

    MIN_BUDGET = 10000
    MIN_REVENUE = 10000   
    MIN_FILMS = 30

    data = df[["id", "genres_TMDB", "budget", "revenue"]]
    data = data[(data["budget"] >= MIN_BUDGET) & (data["revenue"] >= MIN_REVENUE)].copy()
    data["roi"] = data["revenue"] / data["budget"]
    data["log_budget"] = np.log10(data["budget"])
    data["log_revenue"] = np.log10(data["revenue"])

    film_genres = data.explode("genres_TMDB").dropna(subset=["genres_TMDB"])

    stats = (
        film_genres.groupby("genres_TMDB")
        .agg(
            n=("id", "size"),
            budget_median=("budget", "median"),
            revenue_median=("revenue", "median"),
            roi_median=("roi", "median"),
        )
        .query("n >= @MIN_FILMS")
        .sort_values(sort_by)
    )
    print(stats.round(2))

    return film_genres[film_genres["genres_TMDB"].isin(stats.index)], stats


def draw_violins(film_genres, stats):
    """Violons divisés : distributions du budget (haut) et du revenu (bas) par genre."""
    
    # === Données locales
    sns.set_style("white")
    LOG_RANGE = (4, 9.5)   # de 10 k$ à ~3 Md$
    BW_ADJUST = 0.3
    
    # === Création du graphique
    order = stats.index.tolist()
    long = film_genres.melt(
        id_vars=["id", "genres_TMDB"], value_vars=["log_budget", "log_revenue"],
        var_name="grandeur", value_name="log_usd",
    )
    long["grandeur"] = long["grandeur"].map({"log_budget": "Budget", "log_revenue": "Revenu"})
    palette = {"Budget": "#e34933", "Revenu": "#62a32e"}

    grid = sns.FacetGrid(
        long, row="genres_TMDB",
        row_order=order,
        aspect=11, height=1.0,  # Un peu plus haut pour laisser de la place haut/bas
    )
    grid.map_dataframe(
        sns.violinplot, x="log_usd", hue="grandeur", hue_order=["Budget", "Revenu"],
        palette=palette, split=True, inner=None, bw_adjust=BW_ADJUST, cut=0,
        linewidth=1.5, linecolor="white", legend=False
    )

    # === Gestion des axes et des labels
    for genre, ax in grid.axes_dict.items():
        ax.grid(axis="x", linestyle="--", linewidth=0.7, color="#E0E0E0", zorder=0)
        ax.set_axisbelow(True) 
        ax.axhline(0, color="#CCCCCC", linewidth=0.8, zorder=1)
        ax.text(-0.02, 0.5, genre, fontweight="bold", color="#333333",
                ha="right", va="center", transform=ax.transAxes)
    
    USD_TICKS = {4: "10 k$", 5: "100 k$", 6: "1 M$", 7: "10 M$", 8: "100 M$", 9: "1 Md$"}
    grid.set(
        facecolor="none", yticks=[], ylabel="",
        xlim=LOG_RANGE, xticks=list(USD_TICKS), xticklabels=list(USD_TICKS.values()),
    )

    grid.set_titles("")
    grid.set_xlabels("Montant (dollars)")
    grid.figure.suptitle("Budget et revenu par genre cinématographique en échelle logarithmique")
    grid.despine(bottom=True, left=True)
    grid.figure.subplots_adjust(hspace=-0.1, left=0.14, right=0.72, top=0.95)

    # === Légende pour les deux distributions
    grid.figure.legend(
        handles=[Patch(facecolor=c, edgecolor=c, alpha=1, label=l) for l, c in palette.items()],
        title="Distribution", loc="upper left", bbox_to_anchor=(0.74, 0.62),
        frameon=False, fontsize=12, title_fontsize=13, handlelength=2.0, handleheight=1.4, 
        labelspacing=0.6
    )

    plt.show()


def main():
    film_genres, stats = budget_revenue_by_genre(df)
    draw_violins(film_genres, stats)

if __name__ == "__main__":
    main() 
