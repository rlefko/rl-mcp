from logging.config import fileConfig
from os import environ

from alembic import context
from alembic.config import Config
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

load_dotenv(override=True)

from app.api.v1 import Item
from utilities import envs

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("compare_type", "true")

target_metadata = SQLModel.metadata

DATABASE_URL = f"postgresql+psycopg2://{environ.get('DB_USER')}:{environ.get('DB_PASS')}@{environ.get('DB_HOST')}:{environ.get('DB_PORT')}/{environ.get('DB_NAME')}"
config.set_main_option("sqlalchemy.url", DATABASE_URL)


def include_object(object, name, type_, reflected, compare_to):
    if object.info.get("skip_autogenerate", False):
        return False
    else:
        return True


def run_migrations_offline() -> None:
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
