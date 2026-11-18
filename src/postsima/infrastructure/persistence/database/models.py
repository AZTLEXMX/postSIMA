from uuid import UUID

from sqlalchemy import Float, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class StationModel(Base):
    __tablename__ = "stations"

    station_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(5), nullable=True)
    telephone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    municipality: Mapped[str | None] = mapped_column(String(150), nullable=True)
    state: Mapped[str | None] = mapped_column(String(150), nullable=True)
    price: Mapped[str | None] = mapped_column(Text, nullable=True)

    source_records: Mapped[list["SourceRecordModel"]] = relationship(
        back_populates="station",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="SourceRecordModel.id",
    )
    chargers: Mapped[list["StationChargerModel"]] = relationship(
        back_populates="station",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="StationChargerModel.id",
    )


class SourceRecordModel(Base):
    __tablename__ = "source_records"
    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_source_external_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    station_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("stations.station_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source: Mapped[int] = mapped_column(Integer, nullable=False)
    external_id: Mapped[str] = mapped_column(String(150), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    telephone: Mapped[str | None] = mapped_column(String(100), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    price: Mapped[str | None] = mapped_column(Text, nullable=True)

    station: Mapped["StationModel"] = relationship(back_populates="source_records")
    chargers: Mapped[list["SourceRecordChargerModel"]] = relationship(
        back_populates="source_record",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="SourceRecordChargerModel.id",
    )


class StationChargerModel(Base):
    __tablename__ = "station_chargers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    station_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("stations.station_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    connector_type: Mapped[str] = mapped_column(String(25), nullable=False)
    power_kw: Mapped[float | None] = mapped_column(Float, nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    station: Mapped["StationModel"] = relationship(back_populates="chargers")


class SourceRecordChargerModel(Base):
    __tablename__ = "source_record_chargers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_record_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("source_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    connector_type: Mapped[str] = mapped_column(String(25), nullable=False)
    power_kw: Mapped[float | None] = mapped_column(Float, nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    source_record: Mapped["SourceRecordModel"] = relationship(
        back_populates="chargers"
    )