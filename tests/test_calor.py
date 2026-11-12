import numpy as np
import pandas as pd
import pytest

from calor.analysis import city_summary, hot_days_per_year, hot_threshold, trend_per_decade


def city(name="Ciudad", base=25.0, heat_wave_from=None):
    """Daily temperatures 1980-2025.

    Every year: 30 warm days at base + 10 (about 8% of the year, so they set the
    threshold) and the rest at `base`. From `heat_wave_from` on, ten extra days
    per year reach base + 15, above anything in the reference period.
    """
    dates = pd.date_range("1980-01-01", "2025-12-31", freq="D")
    tmax = np.full(len(dates), base)
    tmax[dates.day_of_year <= 30] = base + 10
    if heat_wave_from:
        tmax[(dates.year >= heat_wave_from) & dates.day_of_year.isin(range(100, 110))] = base + 15
    return pd.DataFrame({"city": name, "date": dates, "tmax": tmax})


def test_threshold_comes_from_the_reference_period_only():
    assert hot_threshold(city(heat_wave_from=2016)) == pytest.approx(hot_threshold(city()))
    assert hot_threshold(city()) == pytest.approx(35.0)


def test_hot_days_must_be_above_the_threshold_not_equal_to_it():
    yearly = hot_days_per_year(city(heat_wave_from=2016)).set_index("year")["hot_days"]
    assert yearly[1995] == 0          # the 35 C days equal the threshold: not counted
    assert yearly[2020] == 10         # the ten 40 C days


def test_each_city_gets_its_own_threshold():
    days = pd.concat([city("Fría", base=15.0), city("Caliente", base=30.0)])
    thresholds = hot_days_per_year(days).groupby("city")["threshold_c"].first()
    assert thresholds["Fría"] == 25.0
    assert thresholds["Caliente"] == 40.0


def test_trend_is_reported_per_decade():
    years = pd.Series(range(2000, 2021))
    assert trend_per_decade(years, 2 * years) == pytest.approx(20.0)


def test_summary_compares_the_1980s_with_the_last_decade():
    summary = city_summary(city(heat_wave_from=2016)).iloc[0]
    assert summary["hot_days_1980s"] == 0
    assert summary["hot_days_2016_2025"] == 10
    assert summary["extra_hot_days_per_decade"] > 0
    assert summary["warming_of_average_max_c"] > 0
