"""Alembic environment configuration for multi-schema, multi-context migrations.

Each bounded context owns its own PostgreSQL schema and migration history.
Migration scripts are organized in separate directories per context:
  - app/alembic/job/versions/     (job schema)
  - app/alembic/company/versions/ (company schema)
  - app/alembic/skill/versions/   (skill schema)
  - app/alembic/shared/versions/  (shared schema)
"""

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

_server_dir = os.path.join(os.path.dirname(__file__), '..', 'server')
sys.path.insert(0, os.path.abspath(_server_dir))

from shared.infrastructure.config.app_config import DATABASE_URL
from shared.infrastructure.database.sqlalchemy_config import Base

from shared.infrastructure.database import models  # noqa: F401

config = context.config
config.set_main_option('sqlalchemy.url', DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def include_object(obj, name, type_, reflected, compare_to):
    if type_ == "table":
        schema = getattr(obj, "schema", None)
        if schema and context.get_context().get("schema") and schema != context.get_context().get("schema"):
            return False
    return True


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            version_table="alembic_version",
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()