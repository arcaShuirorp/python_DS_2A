import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import seaborn as sns
from scipy import stats


def plot_films_par_annee(films):
    annees = pd.to_numeric(films["startYear_IMDb"], errors="coerce")
    if annees.notna().sum() == 0 and "release_date" in films.columns:
        annees = pd.to_datetime(films["release_date"], errors="coerce").dt.year

    par_an = annees.dropna().astype(int).value_counts().sort_index()

    plt.figure(figsize=(14, 5))
    plt.bar(par_an.index, par_an.values, width=0.9)
    plt.title("Nombre de films par année de sortie")
    plt.xlabel("Année")
    plt.ylabel("Nombre de films")
    plt.tight_layout()
    plt.show()


def plot_notes_imdb_tmdb(films):
    
    # === Mise en forme des données
    notes = pd.DataFrame({
        "IMDb": pd.to_numeric(films["averageRating_IMDb"], errors="coerce"),
        "TMDB": pd.to_numeric(films["vote_average_TMDB"], errors="coerce"),
    })
    notes["TMDB"] = notes["TMDB"].where(notes["TMDB"] > 0)   
    notes = notes.dropna()                                   

    corr = notes["IMDb"].corr(notes["TMDB"])
    print(f"Films avec les deux notes : {len(notes):,}")
    print(f"Corrélation IMDb / TMDB : {corr:.3f}")

    # === Création du graphique
    cmap = sns.color_palette("Greens", as_cmap=True)
    dark = cmap(0.85)

    with sns.axes_style("white"):
        g = sns.JointGrid(data=notes, x="IMDb", y="TMDB", height=7, space=0)

    # === Paramètres pour le jointplot avec aplats de couleur façon aura + points
    g.plot_joint(
        sns.kdeplot, fill=True, cmap=cmap, levels=[0.05, 0.2, 0.4, 0.6, 0.8, 1],
        thresh=0.02, clip=((2, 10), (2, 10)),
    )

    sns.scatterplot(
        data=notes, x="IMDb", y="TMDB", ax=g.ax_joint,
        s=10, color=dark, alpha=0.15, linewidth=0,
    )

    # Régression avec bande de confiance à 95% (elle se voit pas mdrrr)
    sns.regplot(
        data=notes, x="IMDb", y="TMDB", scatter=False, ax=g.ax_joint,
        ci=95, n_boot=500, color="#1f2d3d", line_kws=dict(linewidth=2),
    )

    # === Paramètres pour les histos sur les marges 
    g.plot_marginals(
        sns.histplot, color=cmap(0.7), alpha=1, bins=40,
        edgecolor="white", linewidth=1 
    )

    # === Titre labels et axes
    g.ax_joint.set_xlim(2, 10)   
    g.ax_joint.set_ylim(2, 10)
    g.set_axis_labels("Note IMDb", "Note TMDB")
    sns.despine(fig=g.figure, left=True, bottom=True)
    for side in ("left", "bottom"):
        g.ax_joint.spines[side].set_color("#9aa5b1")
        g.ax_joint.spines[side].set_linewidth(1)
    g.ax_joint.tick_params(length=3, color="#9aa5b1")
    g.ax_joint.grid(color="#e6e9ed", linewidth=0.8)
    g.ax_joint.set_axisbelow(True)

    g.figure.suptitle(f"IMDb vs TMDB (corr = {corr:.2f})", y=0.98, fontweight="bold")
    g.figure.subplots_adjust(top=0.92)

    plt.show()



def plot_revenue_vs_notes(films, log_revenue=False):
    revenue = pd.to_numeric(films["revenue"], errors="coerce")
    revenue = revenue.where(revenue > 0)  # 0 = revenu non renseigné

    if log_revenue:
        revenue = np.log10(revenue)
        ylabel = "Revenu (log10 $)"
    else:
        ylabel = "Revenu ($)"

    notes = {
        "Note TMDB": pd.to_numeric(films["vote_average_TMDB"], errors="coerce").where(lambda s: s > 0),
        "Note IMDb": pd.to_numeric(films["averageRating_IMDb"], errors="coerce"),
    }

    palette = sns.color_palette("Greens", 7)

    for (label, note), c_points in zip(notes.items(), [palette[3], palette[4]]):
        data = pd.DataFrame({"note": note, "revenue": revenue}).dropna()

        # Régression linéaire et R²
        reg = stats.linregress(data["note"], data["revenue"])
        r2 = reg.rvalue ** 2

        # Une figure par note
        fig, ax = plt.subplots(figsize=(8, 5))

        sns.regplot(
            data=data, x="note", y="revenue", ax=ax,
            scatter_kws={"s": 8, "alpha": 0.4, "color": c_points},
            line_kws={"color": palette[6], "linewidth": 2},
        )
        ax.text(
            0.05, 0.95,
            f"Coefficient (pente) = {reg.slope:.3g}\n"
            f"Ordonnée à l'origine = {reg.intercept:.3g}\n"
            f"r = {reg.rvalue:.3f}\n"
            f"R² = {r2:.3f}\n"
            f"p-value = {reg.pvalue:.2e}\n"
            f"n = {len(data):,}",
            transform=ax.transAxes, va="top",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
        )
        ax.set_title(f"Revenu en fonction de la {label.lower()}")
        ax.set_xlabel(label)
        ax.set_ylabel(ylabel)

        plt.tight_layout()
        plt.show()
    

def plot_rentabilite_vs_notes(films, log_rentabilite=False, budget_min=10000):
    budget = pd.to_numeric(films["budget"], errors="coerce")
    revenue = pd.to_numeric(films["revenue"], errors="coerce")

    # On garde les films avec un budget > budget_min et un revenu renseigné
    valide = (budget > budget_min) & (revenue > 0)
    rentabilite = (revenue / budget).where(valide)

    if log_rentabilite:
        rentabilite = np.log10(rentabilite)
        ylabel = "Rentabilité (log10 revenu / budget)"
    else:
        ylabel = "Rentabilité (revenu / budget)"

    notes = {
        "Note TMDB": pd.to_numeric(films["vote_average_TMDB"], errors="coerce").where(lambda s: s > 0),
        "Note IMDb": pd.to_numeric(films["averageRating_IMDb"], errors="coerce"),
    }

    palette = sns.color_palette("Greens", 7)

    for (label, note), c_points in zip(notes.items(), [palette[3], palette[4]]):
        data = pd.DataFrame({"note": note, "rentabilite": rentabilite}).dropna()

        # Régression linéaire et R²
        reg = stats.linregress(data["note"], data["rentabilite"])
        r2 = reg.rvalue ** 2

        # Une figure par note
        fig, ax = plt.subplots(figsize=(8, 5))

        sns.regplot(
            data=data, x="note", y="rentabilite", ax=ax,
            scatter_kws={"s": 8, "alpha": 0.4, "color": c_points},
            line_kws={"color": palette[6], "linewidth": 2},
        )
        ax.text(
            0.05, 0.95,
            f"Coefficient (pente) = {reg.slope:.3g}\n"
            f"Ordonnée à l'origine = {reg.intercept:.3g}\n"
            f"r = {reg.rvalue:.3f}\n"
            f"R² = {r2:.3f}\n"
            f"p-value = {reg.pvalue:.2e}\n"
            f"n = {len(data):,}",
            transform=ax.transAxes, va="top",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
        )
        ax.set_title(f"Rentabilité en fonction de la {label.lower()}")
        ax.set_xlabel(label)
        ax.set_ylabel(ylabel)

        plt.tight_layout()
        plt.show()