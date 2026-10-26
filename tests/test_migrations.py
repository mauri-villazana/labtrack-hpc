from alembic import command
from sqlalchemy import inspect, text

from app.db import make_engine
from tests.conftest import migration_config


def test_migrations_match_models_and_are_repeatable(database_url):
    config = migration_config(database_url)
    command.upgrade(config, "head")
    command.upgrade(config, "head")
    command.check(config)
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    engine = make_engine(database_url)
    assert {"users", "projects", "experiments", "auth_sessions"}.issubset(
        inspect(engine).get_table_names()
    )
    engine.dispose()


def test_status_migration_preserves_existing_experiments(tmp_path):
    url = f"sqlite:///{tmp_path / 'legacy.db'}"
    config = migration_config(url)
    command.upgrade(config, "0001")
    engine = make_engine(url)
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO users (id, email, password_hash) "
                "VALUES (1, 'legacy@example.com', 'hash')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO projects (id, user_id, name, description, created_at) "
                "VALUES (1, 1, 'Legacy', '', '2026-01-01 00:00:00')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO experiments "
                "(id, project_id, name, model, dataset_version, metric_name, "
                "metric_value, notes, created_at) "
                "VALUES (1, 1, 'Before migration', 'Model', 'v1', 'F1', 0.8, '', "
                "'2026-01-01 00:00:00')"
            )
        )
    engine.dispose()

    command.upgrade(config, "head")
    command.upgrade(config, "head")
    engine = make_engine(url)
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT name, status FROM experiments WHERE id = 1")
        ).one()
    assert result == ("Before migration", "completed")
    engine.dispose()
