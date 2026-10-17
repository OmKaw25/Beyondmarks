from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable
from app.models import Base


def test_required_tables_compile_for_postgres():
    required = {'users', 'learner_profiles', 'concepts', 'exercises', 'explanation_segments',
                'hypotheses', 'evidence_rules', 'follow_ups', 'follow_up_predictions', 'attempts',
                'learner_evidence', 'hypothesis_assessments', 'learner_challenges',
                'follow_up_selections', 'support_modules', 'support_attempts', 'transfer_tasks',
                'transfer_attempts', 'independent_tasks', 'independent_attempts', 'retention_checks',
                'adaptation_events', 'auth_sessions', 'teacher_assignments', 'teacher_invite_codes'}
    assert required <= set(Base.metadata.tables)
    for table in Base.metadata.sorted_tables:
        assert 'CREATE TABLE' in str(CreateTable(table).compile(dialect=postgresql.dialect()))
    assert Base.metadata.tables['users'].c.username.unique
    assert Base.metadata.tables['attempts'].c.learner_id.foreign_keys


def test_immutable_evidence_has_attempt_and_source():
    table = Base.metadata.tables['learner_evidence']
    assert {'attempt_id', 'evidence_key', 'value_json', 'source', 'created_at'} <= set(table.c.keys())
