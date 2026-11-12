"""Run the whole analysis:  python -m calor"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from .analysis import city_summary, hot_days_per_year
from .data import load

OUTPUT = Path(__file__).resolve().parent.parent / "output"
SURFACE, INK, INK_SECONDARY, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, AXIS, BLUE, ORANGE = "#e1e0d9", "#c3c2b7", "#2a78d6", "#eb6834"
SOURCE = "Fuente: Open-Meteo, reanálisis ERA5 (ECMWF/Copernicus), 1980-2025."


def _frame(fig, title: str, subtitle: str, height: float) -> None:
    fig.text(0.02, 1 - 0.22 / height, title, fontsize=13, fontweight="bold", color=INK, va="top")
    fig.text(0.02, 1 - 0.55 / height, subtitle, fontsize=9.5, color=INK_SECONDARY, va="top")
    fig.text(0.02, 0.12 / height, SOURCE, fontsize=8, color=MUTED, va="bottom")


def then_vs_now(summary: pd.DataFrame, path: Path) -> None:
    """One line per city joining its 1980s value (blue) with today's (orange)."""
    data = summary.sort_values("hot_days_2016_2025")
    height = 0.33 * len(data) + 1.9
    fig, ax = plt.subplots(figsize=(8, height), facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    more = int((data["hot_days_2016_2025"] > data["hot_days_1980s"]).sum())
    _frame(fig, f"Más días de calor extremo en {more} de {len(data)} ciudades",
           "Días al año por encima del umbral de calor extremo de cada ciudad.", height)
    ax.hlines(data["city"], data["hot_days_1980s"], data["hot_days_2016_2025"],
              color=AXIS, linewidth=2, zorder=1)
    ax.scatter(data["hot_days_1980s"], data["city"], s=70, color=BLUE, zorder=2,
               edgecolor=SURFACE, linewidth=1.5, label="1980-1989")
    ax.scatter(data["hot_days_2016_2025"], data["city"], s=70, color=ORANGE, zorder=2,
               edgecolor=SURFACE, linewidth=1.5, label="2016-2025")
    for row in data.itertuples():
        ax.text(max(row.hot_days_1980s, row.hot_days_2016_2025) + 1.5, row.city,
                f"{row.hot_days_2016_2025:.0f} días", va="center", fontsize=9, color=INK)
    ax.set_xlim(0, data[["hot_days_1980s", "hot_days_2016_2025"]].max().max() * 1.15)
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(False)
    ax.tick_params(colors=MUTED, labelsize=9.5, length=0, labelcolor=INK_SECONDARY)
    ax.set_xlabel("Días de calor extremo al año", fontsize=9, color=INK_SECONDARY)
    ax.legend(loc="lower right", frameon=False, fontsize=9, labelcolor=INK_SECONDARY)
    fig.subplots_adjust(left=0.2, right=0.97, top=1 - 0.95 / height, bottom=0.85 / height)
    fig.savefig(path, dpi=160, facecolor=SURFACE)
    plt.close(fig)


def national_trend(yearly: pd.DataFrame, path: Path) -> None:
    """Median across cities of very hot days per year."""
    median = yearly.groupby("year")["hot_days"].median()
    fig, ax = plt.subplots(figsize=(8, 4.2), facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    _frame(fig, "Cada vez más días de calor extremo",
           "Días de calor extremo al año en la ciudad típica (mediana de 18 ciudades). "
           "Línea punteada: promedio 1981-2010.", 4.2)
    ax.bar(median.index, median.to_numpy(), width=0.75, color=BLUE)
    ax.axhline(18.3, color=MUTED, linewidth=1, linestyle=(0, (4, 3)))
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(AXIS)
    ax.tick_params(colors=MUTED, labelsize=9, length=0)
    fig.subplots_adjust(left=0.06, right=0.97, top=0.76, bottom=0.14)
    fig.savefig(path, dpi=160, facecolor=SURFACE)
    plt.close(fig)


def main() -> None:
    (OUTPUT / "charts").mkdir(parents=True, exist_ok=True)
    days = load()
    yearly, summary = hot_days_per_year(days), city_summary(days)
    yearly.to_csv(OUTPUT / "hot_days_by_city_and_year.csv", index=False, encoding="utf-8-sig")
    summary.to_csv(OUTPUT / "city_summary.csv", index=False, encoding="utf-8-sig")
    then_vs_now(summary, OUTPUT / "charts" / "then_vs_now.png")
    national_trend(yearly, OUTPUT / "charts" / "national_trend.png")
    print(summary.to_string(index=False).encode("ascii", "replace").decode())
    median = yearly.groupby("year")["hot_days"].median()
    print("median 1980s:", median.loc[1980:1989].mean(), "median 2016-2025:",
          median.loc[2016:2025].mean(), "top years:", median.nlargest(5).to_dict())


if __name__ == "__main__":
    main()
