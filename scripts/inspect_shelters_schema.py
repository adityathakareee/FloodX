import sys
sys.path.insert(0, 'backend')
from sqlalchemy import create_engine, text
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
with engine.connect() as conn:
    cols = conn.execute(text("""
        SELECT column_name, data_type, is_nullable, column_default 
        FROM information_schema.columns 
        WHERE table_name = 'shelters'
        ORDER BY ordinal_position
    """)).mappings().all()
    for c in cols:
        print(f"{c['column_name']}: {c['data_type']}, nullable={c['is_nullable']}, default={c['column_default']}")

