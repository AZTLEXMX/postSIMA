from uuid import UUID

from sqlalchemy import Engine, select
from sqlalchemy.orm import sessionmaker

from postsima.domain.entities.charger import Charger
from postsima.domain.entities.source_record import SourceRecord
from postsima.domain.entities.station import Station
from postsima.domain.enums.source import Source
from postsima.domain.value_objects.coordinates import Coordinates
from postsima.domain.value_objects.postal_code import PostalCode
from postsima.infrastructure.persistence.database.models import (
    SourceRecordChargerModel,
    SourceRecordModel,
    StationChargerModel,
    StationModel,
)


class SqlAlchemyStationRepository:
    def __init__(self, engine: Engine) -> None:
        self._session_factory = sessionmaker(
            bind=engine,
            expire_on_commit=False,
        )

    def get(self, station_id: UUID) -> Station | None:
        with self._session_factory() as session:
            model = session.get(StationModel, station_id)
            if model is None:
                return None
            return self._to_domain_station(model)

    def find_by_source_record(self, record: SourceRecord) -> Station | None:
        stmt = (
            select(StationModel)
            .join(SourceRecordModel)
            .where(
                SourceRecordModel.source == int(record.source),
                SourceRecordModel.external_id == record.external_id,
            )
        )
        with self._session_factory() as session:
            model = session.scalars(stmt).first()
            if model is None:
                return None
            return self._to_domain_station(model)

    def save(self, station: Station | None) -> None:
        if station is None:
            return

        with self._session_factory() as session:
            existing = session.get(StationModel, station.station_id)
            if existing is None:
                model = self._to_model_station(station)
                session.add(model)
            else:
                existing.name = station.name
                existing.address = station.address
                existing.postal_code = (
                    station.postal_code.value if station.postal_code else None
                )
                existing.telephone = station.telephone
                existing.latitude = (
                    station.coordinates.latitude if station.coordinates else None
                )
                existing.longitude = (
                    station.coordinates.longitude if station.coordinates else None
                )
                existing.municipality = station.municipality
                existing.state = station.state
                existing.price = station.price

                existing.chargers.clear()
                session.flush()
                for charger in station.chargers:
                    existing.chargers.append(
                        StationChargerModel(
                            connector_type=charger.connector_type,
                            power_kw=charger.power_kw,
                            quantity=charger.quantity,
                        )
                    )

                existing.source_records.clear()
                session.flush()
                for record in station.source_records:
                    existing.source_records.append(self._to_model_record(record))

            session.commit()

    def all(self) -> list[Station]:
        stmt = select(StationModel)
        with self._session_factory() as session:
            models = session.scalars(stmt).all()
            return [self._to_domain_station(model) for model in models]

    @classmethod
    def _to_domain_station(cls, model: StationModel) -> Station:
        coordinates = (
            Coordinates(latitude=model.latitude, longitude=model.longitude)
            if model.latitude is not None and model.longitude is not None
            else None
        )
        postal_code = (
            PostalCode(model.postal_code) if model.postal_code else None
        )

        station_kwargs: dict[str, object] = {
            "station_id": model.station_id,
            "name": model.name,
            "address": model.address,
            "postal_code": postal_code,
            "telephone": model.telephone,
            "coordinates": coordinates,
            "municipality": model.municipality,
            "state": model.state,
            "price": model.price,
            "source_records": [
                cls._to_domain_record(rec) for rec in model.source_records
            ],
            "chargers": [
                Charger(
                    connector_type=ch.connector_type,
                    power_kw=ch.power_kw,
                    quantity=ch.quantity,
                )
                for ch in model.chargers
            ],
        }

        return Station(**station_kwargs)

    @staticmethod
    def _to_domain_record(model: SourceRecordModel) -> SourceRecord:
        coordinates = (
            Coordinates(latitude=model.latitude, longitude=model.longitude)
            if model.latitude is not None and model.longitude is not None
            else None
        )
        postal_code = (
            PostalCode(model.postal_code) if model.postal_code else None
        )

        record_kwargs: dict[str, object] = {
            "source": Source(model.source),
            "external_id": model.external_id,
            "name": model.name,
            "address": model.address,
            "postal_code": postal_code,
            "telephone": model.telephone,
            "coordinates": coordinates,
            "price": model.price,
            "chargers": [
                Charger(
                    connector_type=ch.connector_type,
                    power_kw=ch.power_kw,
                    quantity=ch.quantity,
                )
                for ch in model.chargers
            ],
        }

        return SourceRecord(**record_kwargs)

    @classmethod
    def _to_model_station(cls, station: Station) -> StationModel:
        return StationModel(
            station_id=station.station_id,
            name=station.name,
            address=station.address,
            postal_code=(
                station.postal_code.value if station.postal_code else None
            ),
            telephone=station.telephone,
            latitude=(
                station.coordinates.latitude if station.coordinates else None
            ),
            longitude=(
                station.coordinates.longitude if station.coordinates else None
            ),
            municipality=station.municipality,
            state=station.state,
            price=station.price,
            source_records=[
                cls._to_model_record(record) for record in station.source_records
            ],
            chargers=[
                StationChargerModel(
                    connector_type=charger.connector_type,
                    power_kw=charger.power_kw,
                    quantity=charger.quantity,
                )
                for charger in station.chargers
            ],
        )

    @staticmethod
    def _to_model_record(record: SourceRecord) -> SourceRecordModel:
        return SourceRecordModel(
            source=int(record.source),
            external_id=record.external_id,
            name=record.name,
            address=record.address,
            postal_code=(
                record.postal_code.value if record.postal_code else None
            ),
            telephone=record.telephone,
            latitude=(
                record.coordinates.latitude if record.coordinates else None
            ),
            longitude=(
                record.coordinates.longitude if record.coordinates else None
            ),
            price=record.price,
            chargers=[
                SourceRecordChargerModel(
                    connector_type=charger.connector_type,
                    power_kw=charger.power_kw,
                    quantity=charger.quantity,
                )
                for charger in record.chargers
            ],
        )
