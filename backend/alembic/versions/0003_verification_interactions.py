"""Persist distinct transfer, independent, and reflection interactions."""
from pathlib import Path
from alembic import op

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade():
    sql = (Path(__file__).resolve().parents[3] / 'database' / '003_verification_interactions.sql').read_text(encoding='utf-8')
    for statement in sql.split(';'):
        if statement.strip():
            op.execute(statement)


def downgrade():
    raise RuntimeError('Destructive schema rollback is disabled; use a separately approved migration.')
