from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.schema import MetaData

from retrovue.infra.settings import settings

# Deterministic constraint/index names (prevents Alembic churn)
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)

engine = create_engine(
    settings.database_url,
    echo=settings.echo_sql,
    pool_pre_ping=True,
    future=True,
    pool_size=settings.pool_size,
    max_overflow=settings.max_overflow,
    pool_timeout=settings.pool_timeout,
)

@event.listens_for(engine, "connect")
def _set_search_path(dbapi_conn, _):
    with dbapi_conn.cursor() as cur:
        cur.execute("SET search_path TO public")

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
)


# Additional functions for bootstrap infrastructure
def get_engine(db_url: str | None = None) -> Engine:
    """Get or create the database engine."""
    if db_url:
        # Create a new engine with the specified URL
        return create_engine(
            db_url,
            echo=False,
            connect_args={"check_same_thread": False} if "sqlite" in db_url else {}
        )
    return engine


def get_sessionmaker() -> sessionmaker:
    """Get or create the session factory."""
    return SessionLocal


def get_session() -> Generator[Session, None, None]:
    """Get a database session for dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
