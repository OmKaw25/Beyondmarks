"""Composite indexes for learner history and scheduled checks."""
from pathlib import Path
from alembic import op

revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


def upgrade():
    sql = (Path(__file__).resolve().parents[3] / 'database' / '007_history_indexes.sql').read_text(encoding='utf-8')
    for statement in sql.split(';'):
        if statement.strip():
            op.execute(statement)


def downgrade():
    op.drop_index('ix_delayed_checks_learner_due', table_name='delayed_checks')
    op.drop_index('ix_attempts_learner_real_latest', table_name='attempts')
