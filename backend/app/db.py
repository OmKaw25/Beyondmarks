from functools import lru_cache
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from app.config import get_settings
from app.errors import fail


def postgres_url(url: str) -> str:
    if not url:
        fail(503, 'DATABASE_NOT_CONFIGURED', 'The learning database is not connected yet. Configure Supabase to continue.')
    if url.startswith('postgres://'):
        url = 'postgresql://' + url[len('postgres://'):]
    if url.startswith('postgresql://'):
        url = 'postgresql+psycopg://' + url[len('postgresql://'):]
    if not url.startswith('postgresql+psycopg://'):
        fail(503, 'DATABASE_CONFIGURATION', 'Use a PostgreSQL connection URI for the learning database.')
    return url


@lru_cache
def engine_for(url: str, schema: str | None = None):
    schema = schema if schema is not None else get_settings().database_schema
    # Validate explicit operational callers too; never interpolate unchecked SQL.
    schema = get_settings().safe_database_schema(schema)
    engine = create_engine(postgres_url(url), pool_pre_ping=True, connect_args={'connect_timeout': 5}, hide_parameters=True)
    @event.listens_for(engine, 'connect')
    def choose_schema(connection, connection_record):
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO "{schema}"')
        connection.commit()
    return engine


def get_db():
    settings = get_settings()
    engine = engine_for(settings.database_url, settings.database_schema)
    with Session(engine, expire_on_commit=False) as session:
        yield session
