```python
"""
Generic data ingestion and persistence utilities.

This module contains format-level operations only. Dataset-specific
schema validation belongs inside the corresponding dataset package.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd

LOGGER = logging.getLogger(__name__)


def load_csv(
    file_path: str | Path,
    **kwargs: Any,
) -> pd.DataFrame:
    """
    Load a CSV file into a pandas DataFrame.

    Parameters
    ----------
    file_path:
        Path to the CSV file.

    **kwargs:
        Additional keyword arguments passed to ``pandas.read_csv``.
        ``encoding`` defaults to ``utf-8-sig`` and ``low_memory``
        defaults to ``False`` unless explicitly provided.

    Returns
    -------
    pandas.DataFrame
        Loaded data.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.

    ValueError
        If the path is not a file, is not a CSV file, or the CSV
        is empty or cannot be parsed.

    OSError
        If the file cannot be read.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Input file does not exist: {path}"
        )

    if not path.is_file():
        raise ValueError(
            f"Input path is not a file: {path}"
        )

    if path.suffix.lower() != ".csv":
        raise ValueError(
            f"Expected a CSV file, got: {path.suffix or '<no extension>'}"
        )

    kwargs.setdefault("encoding", "utf-8-sig")
    kwargs.setdefault("low_memory", False)

    try:
        dataframe = pd.read_csv(path, **kwargs)

    except pd.errors.EmptyDataError as exc:
        raise ValueError(
            f"CSV file is empty: {path}"
        ) from exc

    except pd.errors.ParserError as exc:
        raise ValueError(
            f"Unable to parse CSV file: {path}"
        ) from exc

    except UnicodeDecodeError as exc:
        raise ValueError(
            f"Unable to decode CSV file using encoding "
            f"{kwargs['encoding']!r}: {path}"
        ) from exc

    except OSError as exc:
        raise OSError(
            f"Unable to read CSV file: {path}"
        ) from exc

    LOGGER.info(
        "Loaded CSV: %s | rows=%d | columns=%d",
        path,
        len(dataframe),
        len(dataframe.columns),
    )

    return dataframe


def save_geodata(
    gdf: gpd.GeoDataFrame,
    output_path: str | Path,
) -> None:
    """
    Save a GeoDataFrame to a supported output format.

    Supported output formats:

    - GeoJSON: ``.geojson`` / ``.json``
    - GeoPackage: ``.gpkg``
    - CSV: ``.csv``

    For CSV output, the geometry column is converted to WKT.

    Existing GeoPackage files are overwritten.

    Parameters
    ----------
    gdf:
        GeoDataFrame to save.

    output_path:
        Destination path.

    Raises
    ------
    TypeError
        If ``gdf`` is not a GeoDataFrame.

    ValueError
        If the output format is unsupported.

    OSError
        If the data cannot be written.
    """
    if not isinstance(gdf, gpd.GeoDataFrame):
        raise TypeError(
            "gdf must be a geopandas.GeoDataFrame."
        )

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    suffix = path.suffix.lower()

    if suffix not in {".geojson", ".json", ".gpkg", ".csv"}:
        raise ValueError(
            "Unsupported output format: "
            f"{suffix or '<no extension>'}. "
            "Supported formats are .geojson, .json, .gpkg and .csv."
        )

    try:
        if suffix in {".geojson", ".json"}:
            gdf.to_file(
                path,
                driver="GeoJSON",
                index=False,
            )

        elif suffix == ".gpkg":
            # Remove the existing file so the output has deterministic
            # overwrite semantics.
            if path.exists():
                path.unlink()

            gdf.to_file(
                path,
                layer="data",
                driver="GPKG",
                index=False,
            )

        elif suffix == ".csv":
            dataframe = gdf.copy()
            geometry_column = gdf.geometry.name

            dataframe[geometry_column] = gdf.geometry.to_wkt()

            dataframe.to_csv(
                path,
                index=False,
                encoding="utf-8",
            )

    except OSError as exc:
        raise OSError(
            f"Unable to save geospatial data to: {path}"
        ) from exc

    except Exception as exc:
        raise OSError(
            f"Unable to save geospatial data to: {path}"
        ) from exc

    LOGGER.info(
        "Saved processed data: %s | rows=%d | columns=%d",
        path,
        len(gdf),
        len(gdf.columns),
    )
