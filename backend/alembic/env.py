from alembic import context
from app.config import get_settings
from app.db import engine_for, postgres_url
from app.models import Base

settings = get_settings()
url = settings.database_url
if context.is_offline_mode():
    context.configure(url=postgres_url(url) if url else 'postgresql+psycopg://', target_metadata=Base.metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    with engine_for(url, settings.database_schema).connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()
