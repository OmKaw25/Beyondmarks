"""Separate student enrollment from teacher referrals."""
from pathlib import Path
from alembic import op
revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None

def upgrade():
    sql = (Path(__file__).resolve().parents[3] / 'database' / '004_student_enrollment.sql').read_text(encoding='utf-8')
    for statement in sql.split(';'):
        if statement.strip(): op.execute(statement)

def downgrade():
    raise RuntimeError('Destructive rollback requires a separately approved migration.')
