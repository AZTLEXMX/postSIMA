import os
from pathlib import Path
from urllib.parse import quote_plus

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from postsima.infrastructure.persistence.database.models import Base

DEFAULT_SQLITE_PATH = (
    Path(__file__).resolve().parents[5] / "data" / "postsima.db"
)


def create_sqlite_engine(db_path: Path | None = None) -> Engine:
    target_path = db_path or DEFAULT_SQLITE_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{target_path}", future=True)
    Base.metadata.create_all(engine)
    return engine


def build_postgres_url_from_env() -> str:
    direct_url = os.getenv("POSTGRES_URL", "").strip()
    if direct_url:
        return direct_url

    user = os.getenv("POSTGRES_USER", "").strip()
    password = os.getenv("POSTGRES_PASSWORD", "").strip()
    host = os.getenv("POSTGRES_HOST", "").strip()
    port = os.getenv("POSTGRES_PORT", "").strip()
    database = os.getenv("POSTGRES_DB", "").strip()

    if not user or not password or not database:
        raise ValueError(
            "Configuration of PostgreSQL database must be set in environment "
            "variables \nDefine correct all parameters of PostgreSQL database"
        )

    encoded_password = quote_plus(password)
    return f"postgresql+psycopg://{user}:{encoded_password}@{host}:{port}/{database}"


def create_postgres_engine(database_url: str | None = None) -> Engine:
    url = database_url or build_postgres_url_from_env()
    engine = create_engine(url, pool_pre_ping=True, future=True)

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise SQLAlchemyError("It was not possible to connect to the database")

    Base.metadata.create_all(engine)
    return engine