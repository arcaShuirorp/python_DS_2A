"""
Ce script traite des données de rentabilité de films par genre, avec en sortie :
    - Une table synthétisant les rentabilités moyennes et médianes par genre
    - Un graphique ridgeline illustrant les densités
"""

# === Importations
import os
from pathlib import Path

from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
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

def visualize_data(df):
    """Fonction pour visualiser le jeu de données"""

    print(df.shape)            # (10000, 38)
    print(df.dtypes)
    print(df.head())
    print(df.info())
    print(df.describe())


def roi_by_genre(df):
    """Calcule des stats sur la rentabilité moyenne d'un film (revenue/budget) par genre de film suffisamment représenté"""

    MIN_BUDGET = 1000
    MIN_FILMS = 30

    data = df[["id", "genres_TMDB", "budget", "revenue"]].copy()
    data = data[(data["budget"] >= MIN_BUDGET) & (data["revenue"] > 0)]
    data["roi"] = data["revenue"] / data["budget"]
    data["log_roi"] = np.log10(data["roi"])

    film_genres = data.explode("genres_TMDB").dropna(subset=["genres_TMDB"])  # une ligne par (film, genre)

    stats = (
        film_genres.groupby("genres_TMDB")
         .agg(
             n=("roi", "size"),
             roi_median=("roi", "median"),
             roi_moyen=("roi", "mean")
         )
         .query("n >= @MIN_FILMS")
         .sort_values("roi_median")
    )
    print(stats.round(2))

    return film_genres[film_genres["genres_TMDB"].isin(stats.index)], stats
    

# === Partie visu

HIGHLIGHTED_MOVIES = {
    597: "Titanic",
    550: "Fight Club",
    289: "Casablanca",
    496243: "Parasite",
    429:  "Le Bon, la Brute et le Truand",
    500:  "Reservoir Dogs",
    346: "Les Sept Samouraïs",
    194: "Le Fabuleux Destin d'Amélie Poulain"
}

def _name_and_color(highlight):
    """Transforme le dico highlight en assignant une couleur par film"""
    
    specs = {}
    DEFAULT_COLORS = sns.color_palette('Dark2', 8)
    
    for i, (film_id, spec) in enumerate(highlight.items()):
        name, color = (spec, None) if isinstance(spec, str) else spec
        specs[film_id] = (name, color or DEFAULT_COLORS[i % len(DEFAULT_COLORS)])
    
    return specs


def plot_films(grid, film_genres, highlight):
    """
    Prend le plot créé par draw_ridgeline() et rajoute des points de couleur au bon endroit 
    correspondant aux films dans highlight
    """

    fig = grid.figure
    specs = _name_and_color(highlight)

    selected = film_genres[film_genres["id"].isin(specs)]
    for film_id in set(specs) - set(selected["id"]):
        print(f"{specs[film_id][0]} : absent (filtré par budget/revenu ?)")

    handles = []
    for film_id, rows in selected.groupby("id"):
        name, color = specs[film_id]
        
        # Logique pour checker si jamais un point sortait du plot
        placed = False
        for _, row in rows.iterrows():
            ax = grid.axes_dict[row["genres_TMDB"]]
            low, high = ax.get_xlim()
            if not low <= row["log_roi"] <= high:
                print(f"{name} : point en dehors de l'axe ({10 ** row['log_roi']:.3g})")
                continue

            fig.add_artist(Line2D(
                xdata=[row["log_roi"]], ydata=[0.25], marker="o", linestyle="", markersize=8,
                markerfacecolor=color, markeredgecolor="#FFFFFF", markeredgewidth=0.8,
                transform=ax.transData, zorder=10,
            ))

            placed = True

        # Garde en mémoire les points plottés pour la légende créée juste après
        if placed:
            handles.append(Line2D([], [], marker="o", linestyle="", markersize=9,
                                  markerfacecolor=color, markeredgecolor="#FFFFFF",
                                  markeredgewidth=0.8, label=name))
    
    # Ajout d'une légende pour chaque point visible
    if handles:
        fig.legend(handles=handles, title="Films", loc="upper left",
                   bbox_to_anchor=(0.740, 0.32), frameon=False,
                   fontsize=8, title_fontsize=9, handletextpad=0.3)

    
def draw_ridgeline(film_genres, stats, cmap_name="Greens_d"):
    """Ridgeline plot assez stylé pour les distributions des rentabilités (en log)"""
   
    # === Données locales 
    sns.set_style("white")
    LOG_RANGE = (-2, 2)
    BW_ADJUST = 0.3  # Lisse + ou - fortement les distributions

    # === Création du graphique
    order = stats.index.tolist() 
    med = stats.loc[order, "roi_median"]
    
        # Gestion de la palette
    cmap = sns.color_palette(cmap_name, as_cmap=True)
    vmin, vmax = np.log10(med.min()), np.log10(med.max())
    norm = Normalize(vmin=vmin, vmax=vmax)
    palette = [cmap(norm(np.log10(m))) for m in med]

    grid = sns.FacetGrid(
            film_genres, row="genres_TMDB", hue="genres_TMDB",
            row_order=order, hue_order=order,
            aspect=22, height=0.5, palette=palette,
    ) 
    grid.map(sns.kdeplot, "log_roi", bw_adjust=BW_ADJUST, clip=LOG_RANGE, clip_on=False, fill=True, alpha=1, linewidth=1.5)
    grid.map(sns.kdeplot, "log_roi", bw_adjust=BW_ADJUST, clip=LOG_RANGE, clip_on=False, color="w", linewidth=2)

    # === Gestion des axes et des labels
    grid.refline(y=0, color="none", linestyle="-", linewidth=2, clip_on=False)
    grid.refline(x=0, color="black", linestyle="--", linewidth=1)

    def label_genre_name(x, color, label):
        ax = plt.gca()
        ax.text(0.01, 0.2, label, fontweight="bold", color=color,
                ha="left", va="center", transform=ax.transAxes)

    grid.map(label_genre_name, "log_roi")

    ticks = list(range(LOG_RANGE[0], LOG_RANGE[1] + 1))
    grid.set(
        facecolor="none",
        yticks=[], ylabel="",
        xlim=LOG_RANGE, xticks=ticks, xticklabels=[rf"$10^{{{t}}}$" for t in ticks]
    )
    
    grid.set_titles("")
    grid.figure.suptitle("Rentabilité par genre cinématographique en échelle logarithmique")
    grid.set_xlabels("Rentabilité (revenue / budget)")
    grid.despine(bottom=True, left=True)

    # === Barre de légende pour les couleurs
    grid.figure.subplots_adjust(hspace=-0.25, left=0.04, right=0.72) 

    cax = grid.figure.add_axes((0.755, 0.35, 0.025, 0.3))
    cbar = grid.figure.colorbar(ScalarMappable(norm=norm, cmap=cmap), cax=cax)
    
        # Labels pour la légende
    cbar_ticks = np.linspace(vmin, vmax, 4)
    cbar.set_ticks(cbar_ticks)
    cbar.set_ticklabels([f"{10**t:.1f}" for t in cbar_ticks])
    cbar.set_label("Rentabilité médiane", labelpad=10)
    cbar.outline.set_visible(False)
    cbar.ax.invert_yaxis()

    plot_films(grid, film_genres, HIGHLIGHTED_MOVIES)

    plt.show()





def main():
    film_genres, stats = roi_by_genre(df)
    draw_ridgeline(film_genres, stats)

main()

