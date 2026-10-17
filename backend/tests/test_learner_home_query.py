"""The learner dashboard reads a bounded latest-per-exercise history."""
from datetime import timedelta
from uuid import uuid4
import pytest
from sqlalchemy import event
from sqlalchemy.orm import Session
from app import models as m
from app.content.catalog import catalog, uid
from app.routers.learning import home

pytestmark = pytest.mark.integration


def test_home_returns_only_latest_owned_real_attempt_per_exercise(integration_engine):
    exercises = catalog()
    timestamp = m.now()
    with Session(integration_engine, expire_on_commit=False) as db:
        user = db.get(m.User, uid('learner_a'))
        attempts = [
            m.Attempt(id=str(uuid4()), learner_id=user.id, exercise_id=exercises[0]['id'], created_at=timestamp-timedelta(days=2)),
            m.Attempt(id=str(uuid4()), learner_id=user.id, exercise_id=exercises[0]['id'], created_at=timestamp, stage='support'),
            m.Attempt(id=str(uuid4()), learner_id=user.id, exercise_id=exercises[1]['id'], created_at=timestamp-timedelta(days=1)),
            m.Attempt(id=str(uuid4()), learner_id=user.id, exercise_id=exercises[0]['id'], created_at=timestamp+timedelta(days=1), is_synthetic=True),
            m.Attempt(id=str(uuid4()), learner_id=uid('learner_b'), exercise_id=exercises[0]['id'], created_at=timestamp+timedelta(days=2)),
        ]
        db.add_all(attempts)
        db.flush()
        statements = []
        def capture(connection, cursor, statement, parameters, context, executemany):
            statements.append(statement)
        event.listen(integration_engine, 'before_cursor_execute', capture)
        try:
            result = home(user, db)['data']
        finally:
            event.remove(integration_engine, 'before_cursor_execute', capture)
        assert [a['id'] for a in result['attempts']] == [attempts[1].id, attempts[2].id]
        assert all(not a['is_synthetic'] for a in result['attempts'])
        assert result['attempts'][0]['concept'] == exercises[0]['name']
        assert result['attempts'][0]['next_url'] == '/support/' + attempts[1].id
        history_queries = [query for query in statements if 'FROM attempts' in query]
        assert len(history_queries) == 1
        assert 'DISTINCT ON' in history_queries[0]
        assert 'JOIN exercises' in history_queries[0] and 'JOIN concepts' in history_queries[0]
        db.rollback()


def test_history_lookup_indexes_exist_in_migrated_database(integration_engine):
    from sqlalchemy import inspect
    inspector = inspect(integration_engine)
    attempts = {index['name']: index for index in inspector.get_indexes('attempts')}
    latest = attempts['ix_attempts_learner_real_latest']
    assert latest['column_names'] == ['learner_id', 'exercise_id', 'created_at', 'id']
    assert 'is_synthetic = false' in latest['dialect_options']['postgresql_where']
    delayed = {index['name']: index for index in inspector.get_indexes('delayed_checks')}
    assert delayed['ix_delayed_checks_learner_due']['column_names'] == ['learner_id', 'due_at', 'id']
