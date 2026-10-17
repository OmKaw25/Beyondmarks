"""Teacher-owned subjects, courses, quizzes, and saved submissions."""
from pathlib import Path
from alembic import op
revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None

def upgrade():
    sql = (Path(__file__).resolve().parents[3] / 'database' / '005_classroom.sql').read_text(encoding='utf-8')
    for statement in sql.split(';'):
        if statement.strip(): op.execute(statement)

def downgrade():
    raise RuntimeError('Destructive rollback requires a separately approved migration.')
