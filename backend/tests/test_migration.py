from pathlib import Path
from app.models import Base


def test_public_tables_have_row_level_security_in_migration():
    sql='\n'.join(p.read_text(encoding='utf-8') for p in sorted((Path(__file__).resolve().parents[2]/'database').glob('00[0-9]_*.sql')))
    for name in Base.metadata.tables:
        assert f'ALTER TABLE {name} ENABLE ROW LEVEL SECURITY;' in sql
