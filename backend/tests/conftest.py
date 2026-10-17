"""Integration tests use an isolated, randomly named PostgreSQL schema."""
from pathlib import Path
import os
from uuid import uuid4
import pytest
from dotenv import dotenv_values
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session
from app.config import get_settings
from app.db import get_db, postgres_url
from app.main import app
from app.seed import seed

ROOT=Path(__file__).resolve().parents[2]


@pytest.fixture(scope='module')
def integration_engine():
    url=os.environ.get('TEST_DATABASE_URL') or dotenv_values(ROOT/'.env').get('TEST_DATABASE_URL')
    if not url:
        pytest.skip('Set TEST_DATABASE_URL for real PostgreSQL integration tests.')
    schema='bm_test_'+uuid4().hex
    admin=create_engine(postgres_url(url),hide_parameters=True,connect_args={'connect_timeout':10})
    with admin.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine=create_engine(postgres_url(url),hide_parameters=True,connect_args={'connect_timeout':10})
    @event.listens_for(engine,'connect')
    def choose_schema(connection, connection_record):
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO "{schema}"')
        connection.commit()
    try:
        sql='\n'.join(p.read_text(encoding='utf-8') for p in sorted((ROOT/'database').glob('00[0-9]_*.sql')))
        with engine.begin() as connection:
            for statement in sql.split(';'):
                if statement.strip():connection.execute(text(statement))
        with Session(engine,expire_on_commit=False) as session:
            seed(session,'integration-password-123')
        yield engine
    finally:
        engine.dispose()
        # Only this run's generated schema is removed; public is never reset.
        assert schema.startswith('bm_test_') and len(schema)==40
        with admin.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin.dispose()


@pytest.fixture
def live_client(integration_engine):
    def sessions():
        with Session(integration_engine,expire_on_commit=False) as session:yield session
    app.dependency_overrides[get_db]=sessions
    get_settings.cache_clear()
    with TestClient(app) as client:yield client
    app.dependency_overrides.clear()
