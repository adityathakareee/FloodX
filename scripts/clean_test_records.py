import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from sqlalchemy import create_engine, text
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
with engine.connect() as conn:
    conn.execute(text("DELETE FROM shelter_update_history WHERE shelter_id IN (SELECT id FROM shelters WHERE name ILIKE '%Test%' OR name ILIKE '%Unauthorized%')"))
    conn.execute(text("DELETE FROM shelters WHERE name ILIKE '%Test%' OR name ILIKE '%Unauthorized%'"))
    conn.execute(text("DELETE FROM road_closures WHERE edge_id ILIKE '%test%'"))
    conn.commit()
    print("Cleaned up test records successfully!")
