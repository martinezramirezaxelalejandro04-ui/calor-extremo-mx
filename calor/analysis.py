"""Count each city's very hot days per year and how that number has changed.

A "very hot day" is defined relative to each city: a day whose maximum
temperature is above the level that only the hottest 5% of days reached in
1981-2010 (the standard 30-year climate reference period). 33 C is an ordinary
day in Hermosillo and an extreme one in Mexico City, so one fixed number for
the whole country would not work.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

REFERENCE = (1981, 2010)
THEN, NOW = (1980, 1989), (2016, 2025)
HOT_QUANTILE = 0.95


def hot_threshold(city_days: pd.DataFrame) -> float:
    """Temperature exceeded on only the hottest 5% of days of the reference period."""
    reference = city_days[city_days["date"].dt.year.between(*REFERENCE)]
    return float(reference["tmax"].quantile(HOT_QUANTILE))


def hot_days_per_year(days: pd.DataFrame) -> pd.DataFrame:
    """One row per city and year: number of very hot days and the threshold used."""
    rows = []
    for city, city_days in days.groupby("city"):
        threshold = hot_threshold(city_days)
        counts = (city_days["tmax"] > threshold).groupby(city_days["date"].dt.year).sum()
        rows.append(pd.DataFrame({"city": city, "year": counts.index,
                                  "hot_days": counts.to_numpy(),
                                  "threshold_c": round(threshold, 1)}))
    return pd.concat(rows, ignore_index=True)


def trend_per_decade(years: pd.Series, values: pd.Series) -> float:
    """Slope of the straight line through the yearly values, in units per decade."""
    return float(np.polyfit(years, values, 1)[0] * 10)


def city_summary(days: pd.DataFrame) -> pd.DataFrame:
    """One row per city: very hot days then vs now, and the trend."""
    yearly = hot_days_per_year(days)
    yearly_mean = (days.assign(year=days["date"].dt.year)
                   .groupby(["city", "year"])["tmax"].mean().reset_index())
    rows = []
    for city, city_years in yearly.groupby("city"):
        then = city_years[city_years["year"].between(*THEN)]["hot_days"].mean()
        now = city_years[city_years["year"].between(*NOW)]["hot_days"].mean()
        temperatures = yearly_mean[yearly_mean["city"] == city]
        warming = (temperatures[temperatures["year"].between(*NOW)]["tmax"].mean()
                   - temperatures[temperatures["year"].between(*THEN)]["tmax"].mean())
        rows.append({
            "city": city,
            "threshold_c": city_years["threshold_c"].iloc[0],
            "hot_days_1980s": round(then, 1),
            "hot_days_2016_2025": round(now, 1),
            "times_more": round(now / then, 1) if then else float("nan"),
            "extra_hot_days_per_decade": round(
                trend_per_decade(city_years["year"], city_years["hot_days"]), 1),
            "warming_of_average_max_c": round(warming, 2),
        })
    return (pd.DataFrame(rows).sort_values("hot_days_2016_2025", ascending=False)
            .reset_index(drop=True))
