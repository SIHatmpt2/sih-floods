"""
Feature engineering for historical flood-event records.
"""

from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd

from ..features import safe_ratio


VULNERABILITY_COLUMNS = [
    "cloudburst",
    "steep_topography",
    "landslide",
    "deforestation",
    "encroachment",
]


def engineer_features(
    gdf: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """
    Engineer deterministic features from flood-event data.

    Features include
    ----------------
    total_affected
        Total number of casualties and victims.

    casualty_victim_ratio
        Ratio of casualties to victims.

    wind_delta
        Change in wind measurement from before to after the event.

    wind_delta_abs
        Absolute wind change.

    vulnerability_score
        Number of observed vulnerability indicators that are active.

    vulnerability_index
        Mean vulnerability across observed vulnerability indicators.

    high_vulnerability_flag
        1 when vulnerability_index is at least 0.60, otherwise 0.

    rain_snowmelt_interaction
        Interaction between rainfall over three weeks and snowmelt.

    waterlevel_vulnerability_interaction
        Interaction between peak water level and vulnerability index.

    Parameters
    ----------
    gdf:
        Input flood-event GeoDataFrame.

    Returns
    -------
    geopandas.GeoDataFrame
        Feature-enriched copy of the input GeoDataFrame.

    Raises
    ------
    TypeError
        If gdf is not a GeoDataFrame.

    ValueError
        If required impact columns are missing.
    """

    if not isinstance(gdf, gpd.GeoDataFrame):
        raise TypeError("gdf must be a GeoDataFrame.")

    result = gdf.copy()

    # ---------------------------------------------------------
    # Validate required columns
    # ---------------------------------------------------------

    required_for_impact = {
        "casualties",
        "victims",
    }

    missing = required_for_impact - set(result.columns)

    if missing:
        raise ValueError(
            "Missing required columns for impact features: "
            f"{sorted(missing)}"
        )

    # ---------------------------------------------------------
    # Convert impact columns to numeric
    # ---------------------------------------------------------

    result["casualties"] = pd.to_numeric(
        result["casualties"],
        errors="coerce",
    )

    result["victims"] = pd.to_numeric(
        result["victims"],
        errors="coerce",
    )

    # ---------------------------------------------------------
    # Human impact
    # ---------------------------------------------------------

    result["total_affected"] = (
        result["casualties"]
        + result["victims"]
    )

    result["casualty_victim_ratio"] = safe_ratio(
        result["casualties"],
        result["victims"],
    )

    # ---------------------------------------------------------
    # Wind features
    # ---------------------------------------------------------

    if {
        "wind_before",
        "wind_after",
    }.issubset(result.columns):

        result["wind_before"] = pd.to_numeric(
            result["wind_before"],
            errors="coerce",
        )

        result["wind_after"] = pd.to_numeric(
            result["wind_after"],
            errors="coerce",
        )

        result["wind_delta"] = (
            result["wind_after"]
            - result["wind_before"]
        )

        result["wind_delta_abs"] = (
            result["wind_delta"].abs()
        )

    # ---------------------------------------------------------
    # Vulnerability features
    # ---------------------------------------------------------

    available = [
        column
        for column in VULNERABILITY_COLUMNS
        if column in result.columns
    ]

    if available:
        vulnerability_values = (
            result[available]
            .apply(
                pd.to_numeric,
                errors="coerce",
            )
            .clip(0, 1)
        )

        # Treat explicitly missing vulnerability indicators
        # as unknown rather than automatically converting them
        # to zero.
        result["vulnerability_score"] = (
            vulnerability_values.sum(
                axis=1,
                min_count=1,
            )
        )

        result["vulnerability_index"] = (
            vulnerability_values.mean(axis=1)
        )

        result["high_vulnerability_flag"] = (
            result["vulnerability_index"]
            >= 0.60
        ).astype("int8")

    # ---------------------------------------------------------
    # Rainfall / snowmelt interaction
    # ---------------------------------------------------------

    if {
        "rain_3weeks",
        "snowmelt",
    }.issubset(result.columns):

        rain = pd.to_numeric(
            result["rain_3weeks"],
            errors="coerce",
        )

        snowmelt = pd.to_numeric(
            result["snowmelt"],
            errors="coerce",
        )

        result["rain_snowmelt_interaction"] = (
            rain * snowmelt
        )

    # ---------------------------------------------------------
    # Water level / vulnerability interaction
    # ---------------------------------------------------------

    if {
        "peak_waterlevel",
        "vulnerability_index",
    }.issubset(result.columns):

        peak_waterlevel = pd.to_numeric(
            result["peak_waterlevel"],
            errors="coerce",
        )

        result[
            "waterlevel_vulnerability_interaction"
        ] = (
            peak_waterlevel
            * result["vulnerability_index"]
        )

    # ---------------------------------------------------------
    # Numerical safety
    # ---------------------------------------------------------

    numeric_columns = result.select_dtypes(
        include=np.number
    ).columns

    result[numeric_columns] = (
        result[numeric_columns]
        .replace(
            [np.inf, -np.inf],
            np.nan,
        )
    )

    return result
