import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context  # type: ignore

# Ensure "src" is on path (adjust if needed)
HERE = os.path.dirname(__file__)
SYS_SRC = os.path.normpath(os.path.join(HERE, "..", "src"))
if SYS_SRC not in sys.path:
    sys.path.insert(0, SYS_SRC)

# Pull your app's settings & metadata
from retrovue.infra.settings import settings
from retrovue.infra.db import Base  # Base.metadata is target_metadata
# Import models so autogenerate can see them
from retrovue.domain.entities import *  # noqa

config = context.config

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def include_object(object, name, type_, reflected, compare_to):
    """Exclude alembic_version table from autogenerate comparisons."""
    if type_ == "table" and name == "alembic_version":
        return False
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = settings.database_url  # <-- ALWAYS use app's DB URL (Postgres)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
        dialect_opts={"paramstyle": "named"},
        version_table="alembic_version",
        version_table_schema="public",
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Force Alembic to use the same URL as the app
    config.set_main_option("sqlalchemy.url", settings.database_url)

    connectable = engine_from_config(
        configuration=config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            version_table="alembic_version",
            version_table_schema="public",
            include_object=include_object,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
