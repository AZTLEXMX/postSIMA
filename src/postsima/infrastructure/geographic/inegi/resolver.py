from pathlib import Path

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

from postsima.application.ports.geographic_resolver import (
    GeographicData,
    GeographicResolver,
)
from postsima.domain.value_objects.coordinates import Coordinates


_MUNICIPALITY_COLUMNS = ("NOMGEO",)
_STATE_COLUMNS = ("NOMGEO_2",)


class InegiGeographicResolver(GeographicResolver):
    def __init__(self, dataset_path: Path) -> None:
        if not dataset_path.is_file():
            raise FileNotFoundError(
                f"Not found geographic file INEGI: {dataset_path}"
            )

        self._data = gpd.read_file(dataset_path)

        if self._data.empty:
            raise ValueError("The INEGI Geographic file doesn't have "
                             "registers registros.")

        if self._data.crs is None:
            raise ValueError("The INEGI Geographic file doesn't define a CRS.")

        self._municipality_column = self._find_column(
            self._data.columns, _MUNICIPALITY_COLUMNS
        )
        self._state_column = self._find_column(
            self._data.columns, _STATE_COLUMNS
        )

        self._spatial_index = self._data.sindex

    def resolve(self, coordinates: Coordinates) -> GeographicData | None:
        point = gpd.GeoSeries(
            [Point(coordinates.longitude, coordinates.latitude)],
            crs="EPSG:4326",
        ).to_crs(self._data.crs).iloc[0]

        candidate_positions = self._spatial_index.query(
            point,
            predicate="intersects",
        )

        for position in candidate_positions:
            row = self._data.iloc[int(position)]

            return GeographicData(
                municipality=self._optional_text(row[self._municipality_column]),
                state=self._optional_text(row[self._state_column]),
            )

        return None

    @staticmethod
    def _find_column(columns, candidates: tuple[str, ...]) -> str:
        normalized = {
            str(column).strip().casefold(): str(column)
            for column in columns
        }

        for candidate in candidates:
            match = normalized.get(candidate.casefold())
            if match is not None:
                return match

        raise ValueError(
            "It was not found a compatible geographic column. "
            f"Compatible columns: {list(columns)}"
        )

    @staticmethod
    def _optional_text(value) -> str | None:
        if value is None or pd.isna(value):
            return None

        text = str(value).strip()
        return text or None